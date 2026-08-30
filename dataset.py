import pandas as pd
import io

# Колонки датасета
# Счётные: order_quantity, sales, discount, discount_value
# Категориальные: order_status, customer, order_date, product_category, product_sub_category

NUMERIC_COLS = ['order_quantity', 'sales', 'discount', 'discount_value']
CATEGORICAL_COLS = ['order_status', 'customer', 'order_date', 'product_category', 'product_sub_category']

df = pd.read_csv('dataset.csv', index_col=0)


def print_report(output):
    # 1. Количество строк и колонок
    output.write(str(df.shape) + '\n\n')

    # 2. Типы данных
    buf = io.StringIO()
    df.info(buf=buf)
    output.write(buf.getvalue() + '\n')

    # 3. Количество незаполненных ячеек
    output.write(df.isnull().sum().to_string() + '\n\n')

    # 4. Статистика по счётным колонкам
    output.write('Колонка>\tсреднее\tмедиана\tотклонение\n')
    for col in NUMERIC_COLS:
        mean = df[col].mean()
        median = df[col].median()
        std = df[col].std()
        output.write(f'{col}>\t{mean:.2f};\t{median:.2f};\t{std:.2f}\n')
    output.write('\n')

    # 5. Уникальные значения и частота для категориальных колонок
    for col in CATEGORICAL_COLS:
        output.write(f'{col}\n')
        output.write(df[col].value_counts().to_string() + '\n\n')


if __name__ == '__main__':
    # Вывод в консоль
    console_output = io.StringIO()
    print_report(console_output)
    report_text = console_output.getvalue()

    print(report_text)

    # Дублирование в файл report.txt
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)