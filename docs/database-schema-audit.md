# Database schema usage audit

Reviewed against the repository on 11 October 2026, before revision
`d7c6a5b4e390`. The ORM and all Alembic revisions were compared with backend
queries/writes, HTTP and WebSocket handlers, seed paths, frontend consumers, and
tests. This inventory describes the schema immediately before cleanup; the
four removed columns are called out below. No table was removed.

## Tables and columns

| Table | Column(s) | Status before cleanup | Current evidence and decision |
| --- | --- | --- | --- |
| `categories` | `id`, `image_url` | USED | `ingestion.get_category_list` returns both for the category phase; seed imports images. Keep. |
| `category_translations` | `category_id`, `language_code`, `name` | USED | `ingestion.get_category_list` filters translations by room language; `users.utils.get_user_category_analytics` translates category names. Keep. |
| `questions` | `id`, `category_id`, `language_code`, `question_text`, `correct_answer`, `image_url` | USED | `ingestion.get_random_question` filters and returns question data for the engine; seed importer writes all fields. Keep. |
| `question_decoys` | `id`, `question_id`, `decoy_text` | USED or INDIRECTLY USED (`id`) | `get_random_question` loads decoys through the relationship; `id` identifies ORM rows. Keep. |
| `users` | `id`, `username`, `email`, `avatar_url` | USED | Authentication, profile, friend/invitation queries, WebSocket identity, and history participants. Keep. |
| `users` | `password_hash`, `google_sub`, `auth_version` | USED | Password/Google login, token version checks, and reset. Keep. |
| `users` | `username_key`, `email_key` | USED | Casefold identity lookups and duplicate protection. Keep. |
| `users` | `reset_digest`, `reset_expires`, `reset_sent_at` | USED | `authentication.password_reset` checks token expiry and request cooldown. Keep. |
| `users` | `cover_url`, `created_at` | USED | `users.utils.build_user_profile` returns banner and joined date. `cover_url` has no current write route, but stored values affect the API and frontend profile banner. Keep. |
| `games` | `id`, `total_rounds`, `finished_at` | USED | `events.podium` saves completed matches through `services.save_game_results`; `users.utils.get_user_game_history` reads these fields. Keep. |
| `games` | `host_user_id`, `started_at` | INDIRECTLY USED | Host ownership FK and `check_game_valid_dates` depend on them; the live save path supplies both. Keep. |
| `games` | `language_code` | CURRENTLY UNUSED after write | The save helper and mock seeder supplied it; no history, profile, API, or other query read it. Removed. |
| `game_player_results` | `game_id`, `user_id`, `final_score`, `final_rank` | USED | Save helper, game history, profile totals, and category-results FK. Keep. |
| `game_player_results` | `bluff_votes_received` | CURRENTLY UNUSED after write | Live podium and mock seed supplied it; profile analytics reads the category-level count instead. Removed. |
| `game_player_category_results` | `game_id`, `user_id`, `category_id`, `questions_played`, `correct_answers`, `bluff_votes_received` | USED by API; live writes absent | `get_user_category_analytics` reads all six fields, and `services.save_game_results` can save them. Live podium passes an empty list; mock seeding populates category data. Keep the table and every column. |
| `friendships` | `requester_id`, `receiver_id`, `status`, `created_at` | USED | `friendship.repository` handles request state, search, and notifications; `invitations.repository.are_friends` checks accepted pairs. Keep. |
| `room_invitations` | `id`, `sender_id`, `recipient_id`, `room_code`, `status`, `created_at`, `expires_at` | USED | `invitations.repository` creates, lists, expires, serializes, and updates invitations; router checks live rooms. Keep. |
| `user_achievements` | `user_id`, `achievement_code`, `unlocked` | USED | `achievement_persistence` saves/loads unlocks; profile maps stored true rows to current definitions. Keep. |
| `user_achievements` | `description`, `img` | CURRENTLY UNUSED after write | Persistence and mock seeding wrote them, but the profile response uses `ACHIEVEMENT_DEFINITIONS` for both values. Removed. |

## Keys, foreign keys, checks, and indexes

All primary keys were kept: single `id` keys on categories, questions, decoys,
users, games, and invitations; `(category_id, language_code)` on translations;
`(game_id, user_id)` on player results; `(game_id, user_id, category_id)` on
category results; `(requester_id, receiver_id)` on friendships; and
`(user_id, achievement_code)` on achievements. They identify ORM rows or
support conflict handling. All foreign keys were kept: translation → category,
question → category, decoy → question, game → host user, player result → game
and user, category result → player result and category, friendship → both
users, invitation → sender and recipient, and achievement → user.

| Constraint or index | Status | Evidence and decision |
| --- | --- | --- |
| Translation `(language_code, name)` and decoy `(question_id, decoy_text)` unique constraints | INDIRECTLY USED | Prevent duplicate seed data and protect language/question semantics. Keep. |
| `users.username`, `email`, `google_sub`, `username_key`, `email_key` unique constraints and auth-method check | INDIRECTLY USED | Protect account identity and valid login methods, including concurrent writes. Keep. |
| `ix_users_reset_digest` | USED | Password reset looks up the digest. Keep. |
| `ix_questions_category_language` | USED | Question selection filters by both columns. Keep. |
| `check_game_valid_dates`, `check_game_total_rounds`, `ix_games_host_user_id` | INDIRECTLY USED | Validate persisted games and support host FK access. No proven safe index removal. Keep. |
| Player-result nonnegative score/rank checks and `ix_game_player_results_user_id` | USED | History/profile filter on user and depend on valid persisted results. Keep. |
| `check_game_player_result_bluff_votes` | CURRENTLY UNUSED after column removal | Constrained only the removed aggregate column. Removed before dropping it. |
| Category-result composite FK, three count checks, and `ix_player_category_results_user_category` | USED or INDIRECTLY USED | Profile analytics filters by user and category; checks and FK protect those rows. Keep. |
| Friendship non-self/status checks, receiver index, and unordered-pair unique index | USED or INDIRECTLY USED | Repository relies on state values and unordered pair conflict handling. Keep. |
| Invitation status check, recipient/status index, and active-invitation partial unique index | USED or INDIRECTLY USED | Listing/expiry filters by recipient/status; unique index rejects duplicate pending invitations. Keep. |

## Safe removals and limits

For each candidate, searches covered ORM fields, SQLAlchemy expressions, raw
SQL, services, authentication, users, engine, achievements, friendships,
invitations, seed scripts, HTTP/WebSocket schemas, frontend API/WebSocket use,
tests, and all migrations. The likely original purposes below are inferences
from names and write paths, not documented design decisions.

| Removed item | Stored / likely purpose | Why current code does not need it | Removal impact |
| --- | --- | --- | --- |
| `games.language_code` | Match language, likely intended for history filtering/display. | The live save helper and mock seeder were the only writers; history queries and responses never read the stored language. Room language still controls question selection. | Historical language data is lost. No current frontend/API field or test reads it; the save helper and mock seed were updated. |
| `game_player_results.bluff_votes_received` | Total bluff votes per player per match, likely intended for aggregate statistics. | The live podium wrote it, but profile analytics reads `game_player_category_results.bluff_votes_received`. Round scores and achievements use in-memory round statistics. | Match-wide totals are lost. No current frontend/API reads them; the podium test and save/seed paths were updated. |
| `user_achievements.description` | Text snapshot of an unlocked achievement, likely intended for display. | The profile API builds its description from `ACHIEVEMENT_DEFINITIONS`, keyed by code. Stored descriptions are never selected. | Stored text snapshots are lost. The frontend continues receiving definition text; unlock writer and mock seed were updated. |
| `user_achievements.img` | Image-path snapshot of an achievement, likely intended for display. | The profile API builds its image path from `ACHIEVEMENT_DEFINITIONS`, keyed by code. Stored paths are never selected. | Stored image-path snapshots are lost. The frontend continues receiving definition paths; unlock writer and mock seed were updated. |

Category-level bluff votes remain in the schema for profile analytics.

The migration permanently discards any existing values in those four columns.
Its downgrade restores the old shape with placeholder data (`en`, `0`, and empty
achievement metadata), so it cannot recover historical values. No development
or test-only table was removed. Whether external, non-repository consumers use
these columns cannot be established from this checkout; the audit's scope is the
current project code.
