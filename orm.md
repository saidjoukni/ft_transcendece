<div dir="rtl">

## أهم عناصر SQLAlchemy المستخدمة في `models.py`

<table dir="rtl">
<thead>
<tr>
<th align="right">العنصر</th>
<th align="right">الشرح</th>
</tr>
</thead>

<tbody>

<tr>
<td><code dir="ltr">Mapped[...]</code></td>
<td>يحدد نوع الخاصية التي نتعامل معها داخل مكتبة <code dir="ltr">SQLAlchemy ORM</code>.</td>
</tr>

<tr>
<td><code dir="ltr">mapped_column(...)</code></td>
<td>يعرّف عموداً داخل جدول قاعدة البيانات.</td>
</tr>

<tr>
<td><code dir="ltr">primary_key=True</code></td>
<td>يجعل العمود مفتاحاً رئيسياً يميز كل سجل داخل الجدول.</td>
</tr>

<tr>
<td><code dir="ltr">autoincrement=True</code></td>
<td>يجعل قاعدة البيانات تزيد الرقم تلقائياً، مثل <code dir="ltr">1, 2, 3</code>.</td>
</tr>

<tr>
<td><code dir="ltr">nullable=False</code></td>
<td>يعني أن القيمة إجبارية ولا يمكن أن تكون <code dir="ltr">NULL</code>.</td>
</tr>

<tr>
<td><code dir="ltr">nullable=True</code></td>
<td>يعني أن القيمة اختيارية ويمكن أن تكون <code dir="ltr">NULL</code>.</td>
</tr>

<tr>
<td><code dir="ltr">unique=True</code></td>
<td>يمنع تكرار نفس القيمة في أكثر من سجل.</td>
</tr>

<tr>
<td><code dir="ltr">index=True</code></td>
<td>ينشئ فهرساً يساعد على تسريع البحث في قاعدة البيانات.</td>
</tr>

<tr>
<td><code dir="ltr">default=...</code></td>
<td>يحدد قيمة افتراضية من جهة <code dir="ltr">Python / SQLAlchemy</code>.</td>
</tr>

<tr>
<td><code dir="ltr">server_default=...</code></td>
<td>يحدد قيمة افتراضية من جهة قاعدة البيانات نفسها، مثل <code dir="ltr">PostgreSQL</code>.</td>
</tr>

<tr>
<td><code dir="ltr">ForeignKey("table.column")</code></td>
<td>يربط عموداً بعمود موجود في جدول آخر.</td>
</tr>

<tr>
<td><code dir="ltr">ondelete="CASCADE"</code></td>
<td>عند حذف السجل الأب، تقوم قاعدة البيانات بحذف السجلات التابعة المرتبطة به أيضاً.</td>
</tr>

<tr>
<td><code dir="ltr">ondelete="RESTRICT"</code></td>
<td>يمنع حذف السجل الأب إذا كانت هناك سجلات أخرى ما زالت مرتبطة به.</td>
</tr>

<tr>
<td><code dir="ltr">relationship(...)</code></td>
<td>يسمح بالتنقل بين الكائنات المرتبطة داخل <code dir="ltr">Python / ORM</code>.</td>
</tr>

<tr>
<td><code dir="ltr">back_populates="..."</code></td>
<td>يربط العلاقة من الجهتين داخل <code dir="ltr">SQLAlchemy</code>.</td>
</tr>

<tr>
<td><code dir="ltr">cascade="all, delete-orphan"</code></td>
<td>يجعل <code dir="ltr">SQLAlchemy</code> يدير العمليات التابعة للسجل الأب، ويمكنه حذف سجل تابع لم يعد مرتبطاً بالأب.</td>
</tr>

<tr>
<td><code dir="ltr">passive_deletes=True</code></td>
<td>يجعل <code dir="ltr">SQLAlchemy</code> يعتمد على قاعدة البيانات لتنفيذ عمليات الحذف المرتبطة.</td>
</tr>

<tr>
<td><code dir="ltr">foreign_keys=[...]</code></td>
<td>يحدد أي مفتاح خارجي يجب استعماله عندما توجد أكثر من علاقة ممكنة.</td>
</tr>

<tr>
<td><code dir="ltr">UniqueConstraint(...)</code></td>
<td>يمنع تكرار قيمة أو مجموعة من القيم داخل الجدول.</td>
</tr>

<tr>
<td><code dir="ltr">CheckConstraint(...)</code></td>
<td>يفرض شرطاً يجب أن تحترمه البيانات قبل قبولها في قاعدة البيانات.</td>
</tr>

<tr>
<td><code dir="ltr">Index(...)</code></td>
<td>ينشئ فهرساً مخصصاً على عمود واحد أو أكثر لتسريع البحث.</td>
</tr>

<tr>
<td><code dir="ltr">ForeignKeyConstraint(...)</code></td>
<td>ينشئ علاقة مفتاح خارجي تعتمد على أكثر من عمود.</td>
</tr>

<tr>
<td><code dir="ltr">String(50)</code></td>
<td>يخزن نصاً بحد أقصى محدد، وهنا الحد هو <code dir="ltr">50</code> حرفاً.</td>
</tr>

<tr>
<td><code dir="ltr">Text</code></td>
<td>يخزن نصاً بدون حد صغير محدد مثل <code dir="ltr">String(50)</code>.</td>
</tr>

<tr>
<td><code dir="ltr">Boolean</code></td>
<td>يخزن قيمة منطقية مثل <code dir="ltr">True</code> أو <code dir="ltr">False</code>.</td>
</tr>

<tr>
<td><code dir="ltr">DateTime(timezone=True)</code></td>
<td>يخزن التاريخ والوقت مع معلومات المنطقة الزمنية.</td>
</tr>

<tr>
<td><code dir="ltr">Uuid(as_uuid=True)</code></td>
<td>يخزن معرفاً من نوع <code dir="ltr">UUID</code> ويتعامل معه <code dir="ltr">Python</code> ككائن <code dir="ltr">UUID</code>.</td>
</tr>

<tr>
<td><code dir="ltr">func.now()</code></td>
<td>يطلب من قاعدة البيانات استعمال الوقت الحالي.</td>
</tr>

<tr>
<td><code dir="ltr">text("0")</code></td>
<td>يمرر تعبيراً مكتوباً بصيغة <code dir="ltr">SQL</code> إلى قاعدة البيانات.</td>
</tr>

<tr>
<td><code dir="ltr">func.least(...)</code></td>
<td>يعيد أصغر قيمة من القيم المعطاة.</td>
</tr>

<tr>
<td><code dir="ltr">func.greatest(...)</code></td>
<td>يعيد أكبر قيمة من القيم المعطاة.</td>
</tr>

<tr>
<td><code dir="ltr">@validates(...)</code></td>
<td>يشغل دالة للتحقق من قيمة معينة أو تعديلها عند تغييرها.</td>
</tr>

<tr>
<td><code dir="ltr">__tablename__</code></td>
<td>يحدد الاسم الحقيقي للجدول داخل قاعدة البيانات.</td>
</tr>

<tr>
<td><code dir="ltr">__table_args__</code></td>
<td>يحتوي على إعدادات الجدول، مثل القيود والفهارس.</td>
</tr>

<tr>
<td><code dir="ltr">postgresql_where=...</code></td>
<td>يضيف شرطاً خاصاً بـ<code dir="ltr">PostgreSQL</code> على الفهرس، ويستعمل مثلاً لإنشاء <code dir="ltr">Partial Index</code>.</td>
</tr>

</tbody>
</table>

</div>
### تقسيم سريع

#### تعريف الأعمدة

- `Mapped`
- `mapped_column`
- `primary_key`
- `autoincrement`
- `nullable`
- `unique`
- `default`
- `server_default`

#### العلاقات

- `ForeignKey`
- `ForeignKeyConstraint`
- `relationship`
- `back_populates`
- `foreign_keys`
- `ondelete`
- `cascade`
- `passive_deletes`

#### حماية البيانات

- `CheckConstraint`
- `UniqueConstraint`

#### تحسين البحث

- `Index`
- `index=True`

#### أنواع البيانات

- `String`
- `Text`
- `Boolean`
- `DateTime`
- `Uuid`

#### أدوات إضافية

- `func.now()`
- `func.least()`
- `func.greatest()`
- `text()`
- `@validates`
- `__tablename__`
- `__table_args__`
- `postgresql_where`