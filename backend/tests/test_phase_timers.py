import asyncio
import json
from time import monotonic
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from starlette.websockets import WebSocket

from app.engine import events
from app.engine.room_manager import RoomManager
from app.engine.room_models import PlayerInfo, Room, RoomMetaData, RoomPhase, RoomSettings
from app.engine.utils import Context, GameError


ROOM_ID = "ROOM01"
QUESTION = {
    "id": 1,
    "question": "Which answer is correct?",
    "correct_answer": "Truth",
    "image_url": None,
    "fake_answers": ["Decoy one", "Decoy two", "Decoy three"],
}


def player(name: str, user_id: int) -> PlayerInfo:
    scope = {
        "type": "websocket", "path": "/", "headers": [], "query_string": b"",
        "scheme": "ws", "server": ("test", 80), "client": ("test", user_id),
        "subprotocols": [],
    }
    return PlayerInfo(
        ws=WebSocket(scope, AsyncMock(), AsyncMock()),
        name=name, db_user_id=user_id,
    )


def room_in_category() -> Room:
    metadata = RoomMetaData(
        host_id="1", settings=RoomSettings(bluff_time=11, vote_time=10),
    )
    metadata.phase.start()
    return Room(
        meta_data=metadata,
        players={
            "1": player("Host", 1),
            "2": player("Player B", 2),
            "3": player("Player C", 3),
        },
    )


def controlled_timers(monkeypatch):
    question_deadline = asyncio.Event()
    other_deadline = asyncio.Event()
    real_sleep = asyncio.sleep

    async def controlled_sleep(duration):
        if 10.5 <= duration <= 11:
            await question_deadline.wait()
        elif 9.5 <= duration <= 10:
            await other_deadline.wait()
        else:
            await real_sleep(duration)

    monkeypatch.setattr(events.asyncio, "sleep", controlled_sleep)
    return question_deadline, other_deadline, real_sleep


def mock_room(monkeypatch):
    monkeypatch.setattr(events, "load_question", AsyncMock(return_value=QUESTION))
    room = room_in_category()
    manager = SimpleNamespace(rooms={ROOM_ID: room}, broadcast=AsyncMock())
    return room, manager


async def enter_question(manager, chooser="2"):
    await events.process_event(manager, ROOM_ID, chooser, "Player B", "GET_QUESTION", {
        "category": {"id": 1, "name": "Science"},
    })


async def bluff(manager, player_id):
    await events.process_event(
        manager, ROOM_ID, player_id, f"Player {player_id}", "SUBMIT_BLUFF",
        {"bluff_answer": f"Fake {player_id}"},
    )


def broadcast_count(manager, event_name):
    return sum(
        call.args[0]["event"] == event_name
        for call in manager.broadcast.await_args_list
    )


def cancel_active_timer(room):
    timer = room.meta_data.timer_task
    if timer is not None and not timer.done():
        timer.cancel()


async def websocket_room(monkeypatch):
    monkeypatch.setattr(events, "load_question", AsyncMock(return_value=QUESTION))
    room = room_in_category()
    sent = {}
    for player_id, player_info in room.players.items():
        transport = AsyncMock()
        ws = WebSocket(
            {"type": "websocket", "path": "/", "headers": [], "query_string": b"",
             "scheme": "ws", "server": ("test", 80),
             "client": ("test", int(player_id)), "subprotocols": []},
            AsyncMock(return_value={"type": "websocket.connect"}), transport,
        )
        await ws.accept()
        player_info.ws = ws
        sent[player_id] = transport
    manager = RoomManager()
    manager.rooms[ROOM_ID] = room
    return room, manager, sent


def websocket_event_count(transport, event_name):
    return sum(
        json.loads(call.args[0]["text"])["event"] == event_name
        for call in transport.await_args_list if "text" in call.args[0]
    )


def test_non_host_question_timer_advances_when_one_bluff_is_missing(monkeypatch):
    async def scenario():
        question_deadline, _, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        await enter_question(manager)
        question_timer = room.meta_data.timer_task
        await bluff(manager, "2")
        await bluff(manager, "3")
        await real_sleep(0)
        question_deadline.set()
        await asyncio.wait_for(question_timer, timeout=1)

        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        assert broadcast_count(manager, "PHASE_VOTING") == 1
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_timer_uses_published_deadline_after_slow_broadcast(monkeypatch):
    async def scenario():
        clock = [100.0]
        sleep_delays = []
        release_question = asyncio.Event()
        hold_vote = asyncio.Event()
        real_sleep = asyncio.sleep

        async def controlled_sleep(duration):
            sleep_delays.append(duration)
            if len(sleep_delays) == 1:
                await release_question.wait()
            else:
                await hold_vote.wait()

        async def delayed_broadcast(*_args):
            clock[0] += 5

        monkeypatch.setattr(events, "monotonic", lambda: clock[0])
        monkeypatch.setattr(events.asyncio, "sleep", controlled_sleep)
        room, manager = mock_room(monkeypatch)
        manager.broadcast.side_effect = delayed_broadcast
        await enter_question(manager)
        question_timer = room.meta_data.timer_task
        assert room.meta_data.phase_deadline == 111
        # The timer task starts after the five-second broadcast delay.
        await real_sleep(0)
        assert sleep_delays[0] == 6
        release_question.set()
        await asyncio.wait_for(question_timer, timeout=1)
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_disconnected_player_missing_bluff_does_not_block_timer(monkeypatch):
    async def scenario():
        question_deadline, _, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        room.players["3"].is_present = False
        await enter_question(manager)
        timer = room.meta_data.timer_task
        await bluff(manager, "1")
        await bluff(manager, "2")
        assert len(room.meta_data.submitted_bluffs) == 2
        await real_sleep(0)
        question_deadline.set()
        await asyncio.wait_for(timer, timeout=1)
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        assert broadcast_count(manager, "PHASE_VOTING") == 1
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_all_bluffs_submit_early_and_cancel_question_timer(monkeypatch):
    async def scenario():
        question_deadline, _, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        await enter_question(manager)
        question_timer = room.meta_data.timer_task
        await real_sleep(0)
        for player_id in ("1", "2", "3"):
            await bluff(manager, player_id)
        await asyncio.wait_for(question_timer, timeout=1)
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        assert broadcast_count(manager, "PHASE_VOTING") == 1
        question_deadline.set()
        await real_sleep(0)
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        assert broadcast_count(manager, "RESULTS_REVEALED") == 0
        cancel_active_timer(room)

    asyncio.run(scenario())


@pytest.mark.parametrize("release_timer_first", [False, True])
def test_last_bluff_and_timer_expiry_advance_only_once(monkeypatch, release_timer_first):
    async def scenario():
        question_deadline, _, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        await enter_question(manager)
        question_timer = room.meta_data.timer_task
        await bluff(manager, "1")
        await bluff(manager, "2")
        await real_sleep(0)
        if release_timer_first:
            question_deadline.set()
            last_bluff = asyncio.create_task(bluff(manager, "3"))
        else:
            last_bluff = asyncio.create_task(bluff(manager, "3"))
            question_deadline.set()
        outcomes = await asyncio.gather(question_timer, last_bluff, return_exceptions=True)
        assert outcomes[0] is None
        if isinstance(outcomes[1], GameError):
            assert outcomes[1].error_code == "INVALID_PHASE"
        else:
            assert outcomes[1] is None
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        assert broadcast_count(manager, "PHASE_VOTING") == 1
        assert broadcast_count(manager, "RESULTS_REVEALED") == 0
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_stale_question_timer_cannot_advance_vote(monkeypatch):
    async def scenario():
        _, _, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        await enter_question(manager)
        for player_id in ("1", "2", "3"):
            await bluff(manager, player_id)
        stale = asyncio.create_task(events.phase_timer(
            manager, Context(room_id=ROOM_ID, user_id="2", user_name="Player B"),
            monotonic(), RoomPhase.QUESTION,
        ))
        await asyncio.wait_for(stale, timeout=1)
        await real_sleep(0)
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        assert broadcast_count(manager, "RESULTS_REVEALED") == 0
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_superseded_timer_cannot_advance_a_new_question(monkeypatch):
    async def scenario():
        _, _, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        await enter_question(manager)
        active_timer = room.meta_data.timer_task
        superseded = asyncio.create_task(events.phase_timer(
            manager, Context(room_id=ROOM_ID, user_id="1", user_name="Host"),
            monotonic(), RoomPhase.QUESTION,
        ))
        await asyncio.wait_for(superseded, timeout=1)
        await real_sleep(0)
        assert room.meta_data.timer_task is active_timer
        assert room.meta_data.phase.current_state == RoomPhase.QUESTION
        assert broadcast_count(manager, "PHASE_VOTING") == 0
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_late_bluff_is_rejected_after_timeout_without_mutation(monkeypatch):
    async def scenario():
        question_deadline, _, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        await enter_question(manager)
        timer = room.meta_data.timer_task
        await bluff(manager, "1")
        await bluff(manager, "2")
        await real_sleep(0)
        question_deadline.set()
        await asyncio.wait_for(timer, timeout=1)
        submitted_before = room.meta_data.submitted_bluffs.copy()
        with pytest.raises(GameError) as captured:
            await bluff(manager, "3")
        assert captured.value.error_code == "INVALID_PHASE"
        assert room.meta_data.submitted_bluffs == submitted_before
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        assert broadcast_count(manager, "PHASE_VOTING") == 1
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_missing_vote_advances_on_non_host_vote_timer(monkeypatch):
    async def scenario():
        _, vote_deadline, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        monkeypatch.setattr(events, "save_achievement_candidates", AsyncMock(return_value={}))
        await enter_question(manager)
        for player_id in ("1", "2", "3"):
            await bluff(manager, player_id)
        vote_timer = room.meta_data.timer_task
        correct_choice = next(
            choice["id"] for choice in room.meta_data.voting_choices
            if choice["is_correct"]
        )
        for player_id in ("1", "2"):
            await events.process_event(
                manager, ROOM_ID, player_id, f"Player {player_id}", "SUBMIT_VOTE",
                {"choice_id": correct_choice},
            )
        await real_sleep(0)
        vote_deadline.set()
        await asyncio.wait_for(vote_timer, timeout=1)
        assert room.meta_data.phase.current_state == RoomPhase.REVEAL
        assert broadcast_count(manager, "RESULTS_REVEALED") == 1

    asyncio.run(scenario())


def test_category_timer_from_non_host_context_advances_to_question(monkeypatch):
    async def scenario():
        _, category_deadline, real_sleep = controlled_timers(monkeypatch)
        room, manager = mock_room(monkeypatch)
        room.meta_data.phase.cycle()
        room.meta_data.phase.cycle()
        room.meta_data.phase.cycle()
        room.meta_data.phase.cycle()
        assert room.meta_data.phase.current_state == RoomPhase.PODIUM
        monkeypatch.setattr(events, "load_categories", AsyncMock(return_value=[
            {"id": 1, "name": "Science", "image_url": None},
        ]))
        await events.process_event(manager, ROOM_ID, "2", "Player B", "NEXT_PHASE", {})
        category_timer = room.meta_data.timer_task
        assert room.meta_data.phase.current_state == RoomPhase.CATEGORY
        await real_sleep(0)
        category_deadline.set()
        await asyncio.wait_for(category_timer, timeout=1)
        assert room.meta_data.phase.current_state == RoomPhase.QUESTION
        assert broadcast_count(manager, "PHASE_QUESTION") == 1
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_three_websocket_clients_receive_voting_when_third_does_not_submit(monkeypatch):
    async def scenario():
        question_deadline, _, real_sleep = controlled_timers(monkeypatch)
        room, manager, sent = await websocket_room(monkeypatch)
        await enter_question(manager)
        timer = room.meta_data.timer_task
        await bluff(manager, "1")
        await bluff(manager, "2")
        await real_sleep(0)
        question_deadline.set()
        await asyncio.wait_for(timer, timeout=1)
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        for transport in sent.values():
            assert websocket_event_count(transport, "PHASE_VOTING") == 1
        reconnect_transport = AsyncMock()
        reconnecting = WebSocket(
            {"type": "websocket", "path": "/", "headers": [], "query_string": b"",
             "scheme": "ws", "server": ("test", 80),
             "client": ("test", 33), "subprotocols": []},
            AsyncMock(return_value={"type": "websocket.connect"}), reconnect_transport,
        )
        reconnecting.state.user_id = "3"
        reconnecting.state.user_name = "Player C"
        reconnecting.state.db_user_id = 3
        await manager.connect(reconnecting, ROOM_ID)
        assert websocket_event_count(reconnect_transport, "PHASE_VOTING") == 1
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_three_websocket_clients_receive_only_one_voting_phase_at_deadline(monkeypatch):
    async def scenario():
        question_deadline, _, real_sleep = controlled_timers(monkeypatch)
        room, manager, sent = await websocket_room(monkeypatch)
        await enter_question(manager)
        timer = room.meta_data.timer_task
        await bluff(manager, "1")
        await bluff(manager, "2")
        await real_sleep(0)
        question_deadline.set()
        near_deadline_submission = asyncio.create_task(bluff(manager, "3"))
        outcomes = await asyncio.gather(timer, near_deadline_submission, return_exceptions=True)
        assert outcomes[0] is None
        assert outcomes[1] is None or (
            isinstance(outcomes[1], GameError)
            and outcomes[1].error_code == "INVALID_PHASE"
        )
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        for transport in sent.values():
            assert websocket_event_count(transport, "PHASE_VOTING") == 1
            assert websocket_event_count(transport, "RESULTS_REVEALED") == 0
        cancel_active_timer(room)

    asyncio.run(scenario())


def test_real_bluff_deadline_broadcasts_voting_to_three_websockets(monkeypatch):
    async def scenario():
        room, manager, sent = await websocket_room(monkeypatch)
        room.meta_data.settings.bluff_time = 10
        await enter_question(manager)
        timer = room.meta_data.timer_task
        await bluff(manager, "1")
        await bluff(manager, "2")
        await asyncio.wait_for(timer, timeout=12)
        assert room.meta_data.phase.current_state == RoomPhase.VOTE
        for transport in sent.values():
            assert websocket_event_count(transport, "PHASE_VOTING") == 1
        cancel_active_timer(room)

    asyncio.run(scenario())
