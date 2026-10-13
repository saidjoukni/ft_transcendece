## 1. علاش استعملنا `PostgreSQL`

استعملنا `PostgreSQL` لأن المشروع فيه بيانات دائمة ومترابطة، مثل المستخدمين، الأسئلة، التصنيفات، نتائج المباريات والإنجازات.

`PostgreSQL` مناسب للمشروع لأنه:

- كيسمح لينا ننظمو البيانات داخل جداول مترابطة.
- كيدعم `Foreign Keys` باش نحافظو على العلاقات بين الجداول.
- كيدعم `Constraints` بحال `UNIQUE` و`CHECK` باش يمنع تخزين بيانات غير صحيحة.
- كيدعم `Indexes` باش يسرّع البحث والوصول إلى البيانات.
- كيدعم `Transactions` باش نحفظو مجموعة من العمليات بشكل آمن، وإذا وقع خطأ ما تبقاش قاعدة البيانات فحالة ناقصة.
- مناسب لتخزين البيانات الدائمة `Persistent Data`.

أما بيانات المباراة المؤقتة، مثل المرحلة الحالية، السؤال الحالي، إجابات اللاعبين والأصوات، فكنحتافظو بها فقط داخل ذاكرة الـ`Backend` أثناء المباراة، لأنها كتكون مطلوبة غير مؤقتاً.

بعد انتهاء المباراة، هاد البيانات المؤقتة ما كنحتاجوهاش، بينما البيانات المهمة والدائمة كتبقى محفوظة داخل `PostgreSQL`.

إذن الدور الأساسي ديال `PostgreSQL` فالمشروع هو تخزين البيانات الدائمة، وتنظيم العلاقات بينها، والحفاظ على صحة البيانات.

## 2. `SQLAlchemy ORM`

`SQLAlchemy ORM` هو طبقة كتربط بين كود `Python` وقاعدة البيانات العلائقية.

الفكرة الأساسية ديال الـ`ORM` هي أنه كيحوّل مفاهيم قاعدة البيانات إلى عناصر مفهومة داخل `Python`:

```text
Python Class  ↔  Table
Object        ↔  Row
Attribute     ↔  Column
```

مثلاً:

```python
class User(Base):
    __tablename__ = "users"
```

هذا يعني:

```text
User class   ↔  users table
User object  ↔  row داخل users
username     ↔  column داخل users
```

بهذه الطريقة، ما كنحتاجوش نكتب `SQL` يدوياً في كل عملية، بل كنخدمو باستعمال `Python Classes` و`Objects`، و`SQLAlchemy` كتتكلف بتحويل هاد العمليات إلى استعلامات `SQL`.

### المكونات الرئيسية

`SQLAlchemy` فيها جوج أجزاء رئيسية:

- `SQLAlchemy Core`: كتوفّر أدوات لبناء وتنفيذ استعلامات `SQL`.
- `SQLAlchemy ORM`: كتسمح لينا نتعاملو مع الجداول باستعمال `Python Classes` و`Objects`.

من أهم العناصر اللي كنستعملوها مع الـ`ORM` هي الـ`Session`.

الـ`Session` كتدير التواصل بين الـ`Python Objects` وقاعدة البيانات، وكتساعدنا نتعاملو مع عمليات بحال:

```text
SELECT
INSERT
UPDATE
DELETE
```

كما كتساعد على تنفيذ مجموعة من العمليات داخل `Transactions`.

### كيفاش كيخدم عندنا

الـflow الأساسي هو:

```text
Python Model
     ↓
Session
     ↓
SQLAlchemy
     ↓
PostgreSQL
```

مثلاً، ملي كننشئو:

```python
game = Game(...)
```

فـ`game` هنا غير `Python Object`.

ملي كنقومو بـ:

```python
session.add(game)
```

الـ`Session` كتبدأ كتتبع هاد الـobject، ومن بعد `SQLAlchemy` كتولّد عملية `INSERT` المناسبة وترسلها إلى `PostgreSQL`.

أما فالقراءة، ملي كنكتب:

```python
select(Question)
```

فـ`SQLAlchemy` كتولّد استعلام `SELECT` مناسب، وكترد لينا البيانات على شكل `Question Objects`.

### علاش استعملناه فالمشروع

استعملنا `SQLAlchemy ORM` لأن المشروع فيه بزاف ديال الجداول المترابطة، بحال:

```text
Users
Games
Game Results
Categories
Questions
Decoys
Achievements
Friendships
```

واستعمال الـ`ORM` ساعدنا على:

- تنظيم التعامل مع الجداول داخل `Python`.
- تمثيل العلاقات بين الجداول باستعمال `Relationships`.
- فصل `Game Logic` على تفاصيل أوامر `SQL`.
- تقليل تكرار الاستعلامات اليدوية.
- التعامل مع `Transactions` بطريقة منظمة.
- استعمال `AsyncSession` بشكل مناسب مع `FastAPI` والـ`WebSocket`.

### ملاحظة

استعمال الـ`ORM` ما كيعنيش أننا ما غاديش نحتاجو `SQL` مباشر نهائياً.

فبعض الحالات المعقدة أو الخاصة بالأداء، نقدر نستعمل:

- `SQLAlchemy Core`
- `Raw SQL`

ولكن فمعظم العمليات العادية ديال المشروع، الـ`ORM` كيخلي التعامل مع قاعدة البيانات أوضح، منظم وأسهل فالصيانة.

### `ForeignKey` و `relationship`

`ForeignKey` كيمثل العلاقة الحقيقية داخل قاعدة البيانات.

مثلاً:

`questions.category_id → categories.id`

هذا يعني أن كل سؤال مرتبط بتصنيف موجود فعلاً في جدول `categories`.

الـ`ForeignKey` كيساعد على الحفاظ على سلامة البيانات، بحيث لا يمكن تخزين `category_id` غير موجود.

أما `relationship` فهي ميزة من `SQLAlchemy ORM` لتسهيل التنقل بين الـObjects داخل Python.

مثلاً:

`question.category_id`

تعطينا معرف التصنيف فقط.

بينما:

`question.category`

تعطينا `Category object` المرتبط بالسؤال.

وباستعمال `back_populates` يمكن التنقل في الاتجاهين:

`question.category`

من السؤال إلى التصنيف.

و:

`category.questions`

من التصنيف إلى جميع الأسئلة التابعة له.

إذن:

`ForeignKey` → علاقة على مستوى قاعدة البيانات.

`relationship` → علاقة على مستوى Python/ORM.

| الحاجة | المعنى البسيط |
|---|---|
| `Mapped[...]` | كيوصف type ديال attribute فـSQLAlchemy ORM |
| `mapped_column(...)` | كينشئ column فالـdatabase |
| `primary_key=True` | هاد column هو المفتاح الرئيسي |
| `autoincrement=True` | الـDB كتزيد الرقم بوحدها: 1, 2, 3... |
| `nullable=False` | القيمة إجبارية، ما تقدرش تكون `NULL` |
| `nullable=True` | القيمة تقدر تكون `NULL` |
| `unique=True` | ما يمكنش جوج rows يكون عندهم نفس القيمة |
| `index=True` | كينشئ index باش البحث يكون أسرع |
| `default=...` | default كيحددو Python/SQLAlchemy |
| `server_default=...` | default كتحددو PostgreSQL نفسه |
| `ForeignKey("table.column")` | كيربط column بcolumn فtable أخرى |
| `ondelete="CASCADE"` | إلا تمسح parent، children المرتبطين به يتمسحو |
| `ondelete="RESTRICT"` | يمنع مسح parent إلا كانو records مرتبطين به |
| `relationship(...)` | كتخليك توصل للـobject المرتبط داخل Python |
| `back_populates="..."` | كيربط `relationship` من الجهتين |
| `cascade="all, delete-orphan"` | SQLAlchemy يتبع parent فالعمليات، وحتى child اللي تفصل على parent يقدر يتمسح |
| `passive_deletes=True` | SQLAlchemy كيخلي الـdatabase تتكلف بالـdelete المرتبط |
| `foreign_keys=[...]` | كتحدد بالضبط أنهي `ForeignKey` تستعمل relationship |
| `UniqueConstraint(...)` | كيدير unique rule على column وحدة أو أكثر |
| `CheckConstraint(...)` | كيدير شرط خاص على البيانات |
| `Index(...)` | كينشئ index مخصص |
| `ForeignKeyConstraint(...)` | `ForeignKey` مركب من أكثر من column |
| `String(50)` | نص بحد أقصى 50 character |
| `Text` | نص بلا حد صغير محدد بحال `String(50)` |
| `Boolean` | `True / False` |
| `DateTime(timezone=True)` | تاريخ ووقت مع timezone |
| `Uuid(as_uuid=True)` | UUID وPython يتعامل معاه كـ`UUID object` |
| `func.now()` | PostgreSQL يحط الوقت الحالي |
| `text("0")` | SQL expression مكتوبة كنص |
| `func.least(...)` | كتجيب أصغر قيمة |
| `func.greatest(...)` | كتجيب أكبر قيمة |
| `@validates(...)` | function كتخدم ملي قيمة معينة كتتغير باش تتحقق منها أو تعدلها |
| `__tablename__` | الاسم الحقيقي ديال table فالـdatabase |
| `__table_args__` | مكان كنحطو فيه constraints وindexes ديال table |
| `postgresql_where=...` | شرط خاص بـPostgreSQL على index |


<div dir="rtl">

## `services.py`

ملف <code dir="ltr">services.py</code> يمثل طبقة وسيطة بين منطق اللعبة وقاعدة البيانات.

ملف <code dir="ltr">models.py</code> يحدد شكل البيانات والجداول، بينما <code dir="ltr">services.py</code> يستعمل هذه النماذج لتنفيذ عمليات القراءة والكتابة.

### `load_categories`

الدالة:

<code dir="ltr">load_categories(language_code)</code>

تفتح جلسة مع قاعدة البيانات ثم تستعمل:

<code dir="ltr">get_category_list()</code>

لجلب قائمة التصنيفات حسب اللغة المطلوبة.

### `load_question`

الدالة:

<code dir="ltr">load_question(category_id, language_code)</code>

تفتح جلسة مع قاعدة البيانات ثم تستعمل:

<code dir="ltr">get_random_question()</code>

لجلب سؤال عشوائي حسب التصنيف واللغة.

### العلاقة مع باقي الملفات

<code dir="ltr">models.py</code>

يحدد شكل البيانات.

<code dir="ltr">ingestion.py</code>

يحتوي على منطق القراءة والمعالجة.

<code dir="ltr">services.py</code>

يوفر واجهة بسيطة لباقي أجزاء المشروع لاستعمال عمليات قاعدة البيانات.

</div>

<div dir="rtl">

## حفظ نتائج المباراة

الدالة <code dir="ltr">save_game_results()</code> مسؤولة عن حفظ النتيجة النهائية للمباراة داخل قاعدة البيانات.

هي لا تحسب النقاط، بل تستقبل النتائج المحسوبة مسبقاً وتحفظها.

### التحقق من البيانات

قبل الحفظ، تتحقق الدالة من بعض القيم مثل:

<code dir="ltr">host_user_id</code>

و:

<code dir="ltr">total_rounds</code>

لمنع حفظ بيانات غير صحيحة.

### Transaction

تستعمل الدالة:

<code dir="ltr">AsyncSessionLocal.begin()</code>

وهذا يفتح جلسة وقاعدة بيانات transaction في نفس الوقت.

جميع عمليات الحفظ داخل هذه transaction تعتبر عملية واحدة.

إذا نجحت جميع العمليات، يتم تنفيذ:

<code dir="ltr">COMMIT</code>

أما إذا وقع خطأ، يتم تنفيذ:

<code dir="ltr">ROLLBACK</code>

وبذلك لا يتم حفظ نصف نتيجة فقط.

### منع التكرار

قبل إنشاء المباراة، يتم البحث عن:

<code dir="ltr">game_id</code>

إذا كانت المباراة موجودة مسبقاً، لا يتم حفظها مرة ثانية.

### حفظ المباراة

يتم إنشاء object من:

<code dir="ltr">Game</code>

ثم إضافته إلى الجلسة باستعمال:

<code dir="ltr">session.add()</code>

### `flush()`

الدالة:

<code dir="ltr">session.flush()</code>

ترسل التغييرات الحالية إلى قاعدة البيانات، لكنها لا تنهي transaction.

أما:

<code dir="ltr">COMMIT</code>

فيؤكد transaction نهائياً.

### حفظ نتائج اللاعبين

يتم إنشاء object من:

<code dir="ltr">GamePlayerResult</code>

لكل لاعب.

ويتم تخزين:

- <code dir="ltr">user_id</code>
- <code dir="ltr">final_score</code>
- <code dir="ltr">final_rank</code>

ثم تضاف النتائج باستعمال:

<code dir="ltr">session.add_all()</code>

### حفظ إحصائيات التصنيفات

يمكن أيضاً تخزين إحصائيات كل لاعب داخل كل تصنيف باستعمال:

<code dir="ltr">GamePlayerCategoryResult</code>

مثل:

- <code dir="ltr">questions_played</code>
- <code dir="ltr">correct_answers</code>
- <code dir="ltr">bluff_votes_received</code>

حالياً، بنية قاعدة البيانات تدعم هذه الإحصائيات، لكن live games لا ترسل category results بعد.

</div>