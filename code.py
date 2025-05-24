import pandas as pd
import streamlit as st
import plotly.express as px

# Загальні налаштування стилю
PAGE_CONFIG = {
    "layout": "wide",
    "page_title": "Аналіз ігрового опитування",
    "page_icon": "🎮"
}
st.set_page_config(**PAGE_CONFIG)

CSS = """
<style>
    .stApp { background-color: #f0f2f6; color: #333333; }
    .stMarkdown h1 { color: #1e3a8a; text-align: center; margin-bottom: 30px; padding-top: 20px; }
    .big-font { font-size: 30px !important; font-weight: bold; color: #1e3a8a; margin: 20px 0 15px; text-align: center; }
    .card h2 { color: #333333; margin-top: 0; }
    .sidebar { background-color: #e0e0e0; padding: 20px; border-right: 1px solid #cccccc; }
    .sidebar h2 { color: #1e3a8a; margin-bottom: 15px; }
    .stMultiSelect label { font-weight: bold; color: #555555; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Завантаження даних
survey_df = pd.read_csv("survey_data_updated.csv", sep=';')
impact_df = pd.read_csv("impact_data_updated.csv")

#Об'єднання даних
merge_key_col = 'ID'
if merge_key_col in survey_df.columns and merge_key_col in impact_df.columns:
    survey_df[merge_key_col] = survey_df[merge_key_col].astype(str)
    impact_df[merge_key_col] = impact_df[merge_key_col].astype(str)
    merged_df = pd.merge(survey_df, impact_df, on=merge_key_col, how='outer')
else:
    st.error(f"Помилка: Стовпець '{merge_key_col}' відсутній в одному або обох DataFrame. Перевірте назви стовпців.")
    st.stop()

#Фільтр за віком 
st.sidebar.header("Фільтри")
if 'Вік' in survey_df.columns:
    survey_df['Вік_cleaned'] = pd.to_numeric(survey_df['Вік'], errors='coerce')
    cleaned_ages = survey_df['Вік_cleaned'].dropna().unique().astype(int)
    cleaned_ages_sorted = sorted(cleaned_ages)

    age_label_map = {age: f"{age} р." for age in cleaned_ages_sorted}
    age_labels = [age_label_map[age] for age in cleaned_ages_sorted]

    # Перемикач "Обрати всі"
    select_all_ages = st.sidebar.checkbox("Обрати всі віки", value=True)

    selected_labels = st.sidebar.multiselect(
        "Фільтрувати за віком:",
        options=age_labels,
        default=age_labels if select_all_ages else []
    )

    # Витяг чисел
    age_filter = [age for age, label in age_label_map.items() if label in selected_labels]
else:
    st.sidebar.warning("Стовпець 'Вік' не знайдено у survey_df. Фільтрація за віком недоступна.")
    age_filter = None
# Фільтрація
if age_filter is not None and 'Вік_cleaned' in survey_df.columns:
    filtered_survey_df = survey_df[survey_df['Вік_cleaned'].isin(age_filter)].copy()
    filtered_merged_df = merged_df[merged_df[merge_key_col].isin(filtered_survey_df[merge_key_col])].copy()
else:
    filtered_survey_df = survey_df.copy()
    filtered_merged_df = merged_df.copy()

if filtered_survey_df.empty:
    st.warning("Немає даних, що відповідають вибраним критеріям фільтрації.")
    st.stop()

# Функція для створення кругових діаграм
def create_pie_chart(data, names_col, values_col, title, pull_values=None):
    fig = px.pie(data, names=names_col, values=values_col, title=title,
                color=names_col, color_discrete_sequence=px.colors.qualitative.T10,
                template='plotly_white', hole=0.2)
    fig.update_traces(textposition='outside', textinfo='percent+label', textfont_size=15,
                        textfont_color='gray', marker=dict(line=dict(color='#000000', width=1)),
                      pull=pull_values if pull_values else [0] * len(data))
    fig.update_layout(showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    return fig

tab1, tab2 = st.tabs(["Популярність ігор", "Вплив ігор"])

# Вкладка 1: Популярність ігор
with tab1:
    st.markdown("<p class='big-font'>Статистика популярності ігор та жанрів</p>", unsafe_allow_html=True)
#Перший ряд 
    col1, col2, col3 = st.columns(3)
    # 1. Чи грає у відеоігри
    if 'Чи грає у відеоігри' in filtered_survey_df:
        play_counts = filtered_survey_df['Чи грає у відеоігри'].value_counts().reset_index(name='Кількість')
        play_counts.columns = ['Відповідь', 'Кількість']
        pull_play = [0.05 if label == 'Так' else 0 for label in play_counts['Відповідь']]
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.plotly_chart(create_pie_chart(play_counts, 'Відповідь', 'Кількість', "Співвідношення гравців до не гравців", pull_play), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # 2. Топ-5 жанрів
    if 'Жанр' in filtered_survey_df:
        genre_counts = filtered_survey_df[filtered_survey_df['Жанр'] != '-']['Жанр'].value_counts().head(5).reset_index(name='Кількість')
        genre_counts.columns = ['Жанр', 'Кількість']
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            if not genre_counts.empty:
                fig_genre_bar = px.bar(genre_counts, x='Жанр', y='Кількість', color='Жанр',
                                        template='plotly_white', color_discrete_sequence=px.colors.qualitative.T10,
                                        title="Топ-5 жанрів", labels={'Кількість': 'Кількість'})
                fig_genre_bar.update_layout(xaxis_title="Жанр", yaxis_title="Кількість",
                                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_genre_bar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    # 3. Топ-5 ігор
    if 'Улюблена гра' in filtered_survey_df:
        games_series = filtered_survey_df[filtered_survey_df['Улюблена гра'] != '-']['Улюблена гра'].str.split(',').explode().str.strip().str.lower()
        game_counts = games_series.value_counts().head(5).reset_index(name='Кількість')
        game_counts.columns = ['Гра', 'Кількість']
        with col3:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            fig_game_bar = px.bar(game_counts, x='Гра', y='Кількість', color='Гра',
                                    template='plotly_white', color_discrete_sequence=px.colors.qualitative.T10,
                                    title="Топ-5 ігор", labels={'Кількість': 'Кількість'})
            fig_game_bar.update_layout(xaxis_title="Гра", yaxis_title="Кількість",
                                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_game_bar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

#Другий ряд
    col1, col2, col3 = st.columns(3)
    # 4. Витрати на ігри
    if 'Витрата грошей' in filtered_survey_df:
        spending_counts = filtered_survey_df['Витрата грошей'].value_counts().reset_index(name='Кількість')
        spending_counts.columns = ['Відповідь', 'Кількість']
        pull_spending = [0.05 if label == 'Так' else 0 for label in spending_counts['Відповідь']]
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.plotly_chart(create_pie_chart(spending_counts, 'Відповідь', 'Кількість', "Витрати на ігри", pull_spending), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    # 5. Топ жанрів за відсотком донатерів
    if 'Жанр' in filtered_merged_df and 'Витрата грошей' in filtered_merged_df:
        genre_donations = filtered_merged_df[filtered_merged_df['Витрата грошей'] == 'Так'].assign(Жанр=filtered_merged_df['Жанр'].str.split(',')).explode('Жанр')
        genre_donations['Жанр'] = genre_donations['Жанр'].str.strip()
        genre_donations = genre_donations[genre_donations['Жанр'] != '-']

        genre_totals = filtered_merged_df.assign(Жанр=filtered_merged_df['Жанр'].str.split(',')).explode('Жанр')
        genre_totals['Жанр'] = genre_totals['Жанр'].str.strip()
        genre_totals = genre_totals[genre_totals['Жанр'] != '-']

        donating_counts = genre_donations['Жанр'].value_counts().reset_index(name='Кількість донатерів')
        donating_counts.columns = ['Жанр', 'Кількість донатерів']
        total_counts = genre_totals['Жанр'].value_counts().reset_index(name='Загальна кількість гравців')
        total_counts.columns = ['Жанр', 'Загальна кількість гравців']

        genre_rates = pd.merge(donating_counts, total_counts, on='Жанр', how='left').fillna(0)
        genre_rates['Відсоток донатерів'] = (genre_rates['Кількість донатерів'] / genre_rates['Загальна кількість гравців']) * 100
        top_genres_percent = genre_rates.sort_values(by='Відсоток донатерів', ascending=False).head(5)

        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            if not top_genres_percent.empty:
                fig_genre_donations_bar = px.bar(top_genres_percent, x='Жанр', y='Відсоток донатерів', color='Жанр',
                                                template='plotly_white', color_discrete_sequence=px.colors.qualitative.T10,
                                                labels={'Відсоток донатерів': 'Відсоток донатерів (%)', 'Жанр': 'Жанр'})
                fig_genre_donations_bar.update_layout(title="Топ жанрів за відсотком донатерів",
                                                    xaxis_title="Жанр", yaxis_title="Відсоток донатерів (%)",
                                                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_genre_donations_bar, use_container_width=True)
            else:
                st.warning("Недостатньо даних для відображення топ жанрів за відсотком донатерів.")
            st.markdown("</div>", unsafe_allow_html=True)
    # 6. Розподіл часу гри
    if 'Час' in filtered_survey_df:
        time_mapping = {'менше 1 години': 0.5, 'близько 1 години': 1, 'близько 2 годин': 2,
                        'близько 3 годин': 3, 'близько 4 годин': 4, '4 години і більше': 5}
        time_counts = filtered_survey_df['Час'].value_counts().reset_index(name='Кількість')
        time_counts.columns = ['Час_текст', 'Кількість']
        time_counts['Час_число'] = time_counts['Час_текст'].map(time_mapping)
        time_counts = time_counts.sort_values(by='Час_число')
        with col3:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            fig_playtime_area = px.area(time_counts, x='Час_число', y='Кількість',
                                        title="Популярність часу, проведеного за іграми",
                                        template='plotly_white',
                                        color_discrete_sequence=px.colors.qualitative.T10,
                                        hover_data={'Час_число': False, 'Час_текст': True, 'Кількість': True})
            fig_playtime_area.update_layout(xaxis=dict(tickvals=list(time_mapping.values()),
                                                        ticktext=list(time_mapping.values()),
                                                        title="Середній час гри за день (години)"),
                                            yaxis_title="Кількість гравців",
                                            plot_bgcolor='rgba(0,0,0,0)',
                                            paper_bgcolor='rgba(0,0,0,0)')
            fig_playtime_area.update_traces(hovertemplate="Час: %{customdata[0]}<br>Кількість: %{y}<extra></extra>")
            st.plotly_chart(fig_playtime_area, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

#Третій ряд
    col1, col2, col3 = st.columns(3)
    # 7. Популярність девайсів
    if 'Девайс' in filtered_survey_df:
        filtered_survey_df['Девайс'] = filtered_survey_df['Девайс'].astype(str)
        platform_series = filtered_survey_df[
            (filtered_survey_df['Девайс'] != '-') &
            (filtered_survey_df['Девайс'].str.lower() != 'nan')
        ]['Девайс'].str.split(',').explode().str.strip().str.lower()
        platform_counts = platform_series.value_counts().reset_index(name='Кількість')
        platform_counts.columns = ['Девайс', 'Кількість']
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            if not platform_counts.empty:
                fig_devices_pie = px.pie(platform_counts, names='Девайс', values='Кількість',
                                        title="Популярність ігрових девайсів", template='plotly_white',
                                        color='Девайс', color_discrete_sequence=px.colors.qualitative.T10,
                                        hole=0.2, height=400)
                fig_devices_pie.update_traces(textposition='outside', textinfo='percent+label',
                                            textfont_size=12, textfont_color='gray',
                                            marker=dict(line=dict(color='#000000', width=1)),
                                             pull=[0.03] * len(platform_counts))
                fig_devices_pie.update_layout(showlegend=True,
                                            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1,
                                                        font=dict(size=11, color="gray")),
                                            margin=dict(t=50, b=0, l=0, r=80),
                                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_devices_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    # 8. Розподіл популярності девайсів за жанрами (%)
    if 'Девайс' in filtered_survey_df and 'Жанр' in filtered_survey_df:
        filtered_survey_df['Девайс'] = filtered_survey_df['Девайс'].astype(str)
        device_genre_df = filtered_survey_df[
            (filtered_survey_df['Девайс'].notna()) &
            (filtered_survey_df['Девайс'].str.lower() != 'інше') &
            (filtered_survey_df['Девайс'] != '-') &
            (filtered_survey_df['Девайс'].str.lower() != 'nan') &
            (filtered_survey_df['Жанр'].notna())
        ].copy()
        device_genre_df['Девайс'] = device_genre_df['Девайс'].str.lower().str.split(',').apply(
            lambda lst: [d.strip() for d in lst])
        device_genre_df['Жанр'] = device_genre_df['Жанр'].str.split(',').apply(
            lambda lst: [g.strip() for g in lst])
        exploded_device_genre_df = device_genre_df.explode('Девайс').explode('Жанр')
        exploded_device_genre_df_filtered = exploded_device_genre_df[exploded_device_genre_df['Жанр'] != '-'].copy()
        genre_device_counts = exploded_device_genre_df_filtered.groupby(['Жанр', 'Девайс']).size().reset_index(
            name='Кількість')
        genre_totals = genre_device_counts.groupby('Жанр')['Кількість'].transform('sum')
        genre_device_counts['Відсоток'] = (genre_device_counts['Кількість'] / genre_totals) * 100
        sorted_genres = sorted(genre_device_counts['Жанр'].unique())
        min_x = -0.5  
        max_x = len(sorted_genres) - 0.5  
        min_y = 0
        max_y = genre_device_counts['Відсоток'].max() * 1.1  

        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            fig_devices_genre_line = px.line(genre_device_counts, x='Жанр', y='Відсоток',
                                                color='Девайс', markers=True,
                                                title="Розподіл популярності девайсів за жанрами (%)",
                                                template='plotly_white',
                                                color_discrete_sequence=px.colors.qualitative.T10,
                                                category_orders={'Жанр': sorted_genres},
                                                labels={'Відсоток': 'Відсоток використання (%)', 'Девайс': 'Девайс'})
            fig_devices_genre_line.update_layout(xaxis_title='Жанр', yaxis_title='Відсоток використання (%)',
                                                    legend_title_text='',
                                                    legend=dict(orientation="h", yanchor="bottom", y=0.9,
                                                                xanchor="center", x=0.5,
                                                                font=dict(size=11, color="gray")),
                                                    plot_bgcolor='rgba(0,0,0,0)',
                                                    paper_bgcolor='rgba(0,0,0,0)',
                                                    xaxis=dict(showgrid=True, gridcolor='lightgray', 
                                                            tickvals=sorted_genres,  
                                                            range=[min_x, max_x]),
                                                    yaxis=dict(showgrid=True, gridcolor='lightgray', range=[min_y, max_y]),
                                                    margin=dict(l=0, r=0, b=0, t=50) # Коригуємо поля
                                                    )
        
            for trace in fig_devices_genre_line.data:
                for x, y in zip(trace.x, trace.y):
                    fig_devices_genre_line.add_shape(
                        type="line",
                        x0=x, y0=0, x1=x, y1=y,
                        line=dict(color="gray", width=0.5, dash="dot"),
                        xref="x", yref="y"
                    )
            
            st.plotly_chart(fig_devices_genre_line, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    # 9. Середній час гри за жанром

    if 'Час' in filtered_survey_df and 'Жанр' in filtered_survey_df:
        time_mapping = {'менше 1 години': 0.5, 'близько 1 години': 1, 'близько 2 годин': 2,
                        'близько 3 годин': 3, 'близько 4 годин': 4, '4 години і більше': 5}
        filtered_survey_df['Час_число'] = filtered_survey_df['Час'].map(time_mapping)
        
        filtered_genre_df = filtered_survey_df[filtered_survey_df['Жанр'] != '-'].copy()
        
        genre_counts = filtered_genre_df['Жанр'].value_counts().reset_index(name='Кількість гравців')
        genre_counts.columns = ['Жанр', 'Кількість гравців']
        avg_time_by_genre = filtered_genre_df.groupby('Жанр')['Час_число'].mean().sort_values().reset_index()
        avg_time_by_genre = pd.merge(avg_time_by_genre, genre_counts, on='Жанр', how='left')
        with col3:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            if not avg_time_by_genre.empty:
                fig_time_genre_bar = px.bar(avg_time_by_genre, x='Жанр', y='Час_число',
                                                title="Середній час гри за жанром", template='plotly_white',
                                                color_discrete_sequence=['#1f77b4'] * len(avg_time_by_genre), 
                                                labels={'Час_число': 'Середній час гри (години)', 'Жанр': 'Жанр'},
                                                hover_data={'Жанр': True, 'Час_число': ':.2f',
                                                            'Кількість гравців': True})
                fig_time_genre_bar.update_layout(xaxis_title="Жанр", yaxis_title="Середній час гри (години)",
                                                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                                    showlegend=False)
                st.plotly_chart(fig_time_genre_bar, use_container_width=True)
            else:
                st.warning("Недостатньо даних для відображення залежності часу від жанру.")
            st.markdown("</div>", unsafe_allow_html=True)
#Вкладка 2: Вплив ігор
with tab2:
    st.markdown("<p class='big-font'>Аналіз впливу відеоігор</p>", unsafe_allow_html=True)
#Перший ряд 
    col1, col2, col3 = st.columns(3)
    # 1. Позитивний вплив відеоігор
    if 'Позитивний вплив' in filtered_merged_df:
        positive_impact_counts = filtered_merged_df['Позитивний вплив'].value_counts().reset_index(
            name='Кількість')
        positive_impact_counts.columns = ['Відповідь', 'Кількість']
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.plotly_chart(create_pie_chart(positive_impact_counts, 'Відповідь', 'Кількість',
                                            "Позитивний вплив відеоігор", pull_values=[0.1, 0, 0, 0]),
                            use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # 2. Негативний вплив відеоігор
    if 'Негативний вплив' in filtered_merged_df:
        negative_impact_counts = filtered_merged_df['Негативний вплив'].value_counts().reset_index(
            name='Кількість')
        negative_impact_counts.columns = ['Відповідь', 'Кількість']
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.plotly_chart(create_pie_chart(negative_impact_counts, 'Відповідь', 'Кількість',
                                            "Негативний вплив відеоігор", pull_values=[0, 0.1, 0, 0]),
                            use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    # 3. Порівняння впливу та респондента
    if 'Респондент' in filtered_survey_df.columns and 'Позитивний вплив' in filtered_survey_df.columns and 'Негативний вплив' in filtered_survey_df.columns:
        general_impact_df = pd.DataFrame({
            'Вплив': ['Позитивний'] * len(filtered_survey_df.loc[(filtered_survey_df['Позитивний вплив'] == 'Так')].index) +
                    ['Негативний'] * len(filtered_survey_df.loc[(filtered_survey_df['Негативний вплив'] == 'Так')].index),
            'Респондент': list(filtered_survey_df.loc[(filtered_survey_df['Позитивний вплив'] == 'Так')]['Респондент']) +
                        list(filtered_survey_df.loc[(filtered_survey_df['Негативний вплив'] == 'Так')]['Респондент'])
        })
        with col3:

            sunburst_df_general = general_impact_df.groupby(['Вплив', 'Респондент']).size().reset_index(name='count')

            fig_general = px.sunburst(
                sunburst_df_general,
                path=['Вплив', 'Респондент'],
                values='count',
                color='Вплив', 
                color_discrete_sequence=px.colors.qualitative.T10,
                title="Загальний вплив"
            )
            fig_general.update_traces(textinfo='label+percent entry',
                                    marker=dict(line=dict(color='black', width=1)))
            fig_general.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_general)
    else:
        st.error("Помилка: Відсутні необхідні стовпці для аналізу загального впливу.")

#Другий ряд 
    col1, col2, col3 = st.columns([3, 2, 2])
    # Порівняння впливу за категоріями впливу

    if 'Категорія позитивного впливу' in filtered_merged_df.columns and 'Категорія негативного впливу' in filtered_merged_df.columns:
        filtered_merged_df['Категорія позитивного впливу'] = filtered_merged_df['Категорія позитивного впливу'].str.strip()
        filtered_merged_df['Категорія негативного впливу'] = filtered_merged_df['Категорія негативного впливу'].str.strip()

        # Перейменовуємо категорію перед обчисленням
        filtered_merged_df['Категорія позитивного впливу'] = filtered_merged_df['Категорія позитивного впливу'].replace('Когнітивні функції здібності', 'Когнітивні функції')
        filtered_merged_df['Категорія негативного впливу'] = filtered_merged_df['Категорія негативного впливу'].replace('Когнітивні функції здібності', 'Когнітивні функції')

        positive_impact_categories = filtered_merged_df['Категорія позитивного впливу'].value_counts().reset_index(name='Кількість')
        positive_impact_categories.columns = ['Категорія', 'Позитивний вплив']
        negative_impact_categories = filtered_merged_df['Категорія негативного впливу'].value_counts().reset_index(name='Кількість')
        negative_impact_categories.columns = ['Категорія', 'Негативний вплив']
        grouped_data = pd.merge(positive_impact_categories, negative_impact_categories, on='Категорія', how='outer').fillna(0)
        melted_data = grouped_data.melt(id_vars='Категорія', value_vars=['Позитивний вплив', 'Негативний вплив'], var_name='Вплив', value_name='Кількість')
        with col1:
            fig_interactive = px.bar(melted_data,
                                    y='Категорія',
                                    x='Кількість',
                                    color='Вплив',
                                    barmode='group',
                                    orientation='h',
                                    title='Порівняння позитивного та негативного впливу за категоріями',
                                    color_discrete_sequence=['#2ca02c', '#d62728'])

            fig_interactive.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(
                    orientation="h",
                    y=0,
                    x=-50
                )
            )
            st.plotly_chart(fig_interactive, use_container_width=True)
    else:
        st.error("Помилка: Відсутні необхідні стовпці для відображення згрупованої стовпчикової")

    #Топ-5 типів позитивного впливу
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if 'Категорія позитивного впливу' in filtered_merged_df.columns and 'Тип позитивного впливу' in filtered_merged_df.columns:
            st.markdown(
                """
                <style>
                div[data-baseweb="select"] > div {
                    border: 1px solid #007bff !important;
                    border-radius: 5px !important;
                    padding: 0.1rem !important; 
                }
                .st-eb {
                    display: flex;
                    align-items: center;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            col_label_pos, col_select_pos = st.columns([1, 3]) 

            with col_label_pos:
                st.markdown('<div style="display: flex; align-items: center; height: 2.5rem;">Категорія:</div>', unsafe_allow_html=True)
            with col_select_pos:
                available_categories = ['Всі категорії'] + list(filtered_merged_df['Категорія позитивного впливу'].dropna().unique())
                selected_category = st.selectbox("", options=available_categories, label_visibility="collapsed")

            if selected_category == 'Всі категорії':
                category_data = filtered_merged_df.dropna(subset=['Тип позитивного впливу'])
                type_counts = category_data['Тип позитивного впливу'].value_counts().nlargest(5).reset_index(name='Кількість')
                title = 'Топ-5 типів позитивного впливу (всі категорії)'
            else:
                category_data = filtered_merged_df[filtered_merged_df['Категорія позитивного впливу'] == selected_category].dropna(subset=['Тип позитивного впливу'])
                type_counts = category_data['Тип позитивного впливу'].value_counts().reset_index(name='Кількість')
                title = f'Розподіл типів позитивного впливу для категорії'
            type_counts.columns = ['Тип впливу', 'Кількість']
            fig_histogram_positive = px.bar(type_counts, x='Тип впливу', y='Кількість',
                                            title=title,
                                            color_discrete_sequence=['#2ca02c'])
            fig_histogram_positive.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=100),
                xaxis_title='Тип впливу',
                yaxis_title='Кількість'
            )
            st.plotly_chart(fig_histogram_positive, use_container_width=True)
        else:
            st.error("Помилка: Відсутні необхідні стовпці для відображення гістограми типів позитивного впливу.")
        st.markdown('</div>', unsafe_allow_html=True)
    #Топ-5 типів негативного впливу
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if 'Категорія негативного впливу' in filtered_merged_df.columns and 'Тип негативного впливу' in filtered_merged_df.columns:
            st.markdown(
                """
                <style>
                div[data-baseweb="select"] > div {
                    border: 1px solid #dc3545 !important;
                    border-radius: 5px !important;
                    padding: 0.1rem !important; 
                }
                .st-eb {
                    display: flex;
                    align-items: center;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            col_label_pos, col_select_pos = st.columns([1, 3])
            with col_label_pos:
                st.markdown('<div style="display: flex; align-items: center; height: 2.5rem;">Категорія:</div>', unsafe_allow_html=True)
            with col_select_pos:
                available_categories = ['Всі категорії'] + list(filtered_merged_df['Категорія негативного впливу'].dropna().unique())
                selected_category = st.selectbox("", options=available_categories, label_visibility="collapsed")
                
            if selected_category == 'Всі категорії':
                category_data = filtered_merged_df.dropna(subset=['Тип негативного впливу'])
                type_counts = category_data['Тип негативного впливу'].value_counts().nlargest(5).reset_index(name='Кількість')
                title = 'Топ-5 типів негативного впливу (всі категорії)'
            else:
                category_data = filtered_merged_df[filtered_merged_df['Категорія негативного впливу'] == selected_category].dropna(subset=['Тип негативного впливу'])
                type_counts = category_data['Тип негативного впливу'].value_counts().reset_index(name='Кількість')
                title = f'Розподіл типів негативного впливу для категорії'

            type_counts.columns = ['Тип впливу', 'Кількість']
            fig_histogram_positive = px.bar(type_counts, x='Тип впливу', y='Кількість',
                                            title=title,
                                            color_discrete_sequence=['#d62728'])
            fig_histogram_positive.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=100),
                xaxis_title='Тип впливу',
                yaxis_title='Кількість'
            )
            st.plotly_chart(fig_histogram_positive, use_container_width=True)
        else:
            st.error("Помилка: Відсутні необхідні стовпці для відображення гістограми типів негативного впливу.")
        st.markdown('</div>', unsafe_allow_html=True)
    col_label_genre, col_select_genre = st.columns([1, 3])

    with col_label_genre:
        st.markdown('<div style="display: flex; align-items: center; height: 2.5rem;">Категорія:</div>', unsafe_allow_html=True)
    with col_select_genre:
        available_genre_categories = ['Всі категорії'] + list(filtered_merged_df['Категорія позитивного впливу'].dropna().unique())
        selected_genre_category2 = st.selectbox("Оберіть категорію", options=available_genre_categories, label_visibility="collapsed", key="genre_category_selector2")

# Третій ряд
    col1, col2 = st.columns(2)
    #Топ-5 жанрів позитивного впливу
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if 'Жанр позитивного впливу' in filtered_merged_df.columns:
            positive_genre_data = filtered_merged_df.dropna(subset=['Жанр позитивного впливу'])
            positive_genre_data_filtered = positive_genre_data[positive_genre_data['Жанр позитивного впливу'] != 'Всі']

            if selected_genre_category2 == 'Всі категорії':
                genre_positive_counts = positive_genre_data_filtered['Жанр позитивного впливу'].value_counts().nlargest(5).reset_index(name='Кількість')
                title_positive_genre = 'Топ-5 жанрів позитивного впливу (всі категорії)'
            else:
                genre_positive_category_data = positive_genre_data_filtered[positive_genre_data_filtered['Категорія позитивного впливу'] == selected_genre_category2]
                genre_positive_counts = genre_positive_category_data['Жанр позитивного впливу'].value_counts().nlargest(5).reset_index(name='Кількість')
                title_positive_genre = f'Топ-5 жанрів позитивного впливу для категорії "{selected_genre_category2}"'

            genre_positive_counts.columns = ['Жанр', 'Кількість']

            fig_positive_genre = px.bar(genre_positive_counts, x='Кількість', y='Жанр', orientation='h',
                                        title=title_positive_genre, color_discrete_sequence=['#2ca02c'])
            fig_positive_genre.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=150, r=20, t=60, b=40),
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_positive_genre, use_container_width=True)
        else:
            st.error("Помилка: Відсутній стовпець 'Жанр позитивного впливу'.")
        st.markdown('</div>', unsafe_allow_html=True)
    #Топ-5 жанрів негативного впливу
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if 'Жанр негативного впливу' in filtered_merged_df.columns:
            negative_genre_data = filtered_merged_df.dropna(subset=['Жанр негативного впливу'])
            negative_genre_data_filtered = negative_genre_data[negative_genre_data['Жанр негативного впливу'] != 'Всі'] 

            if selected_genre_category2 == 'Всі категорії':
                genre_negative_counts = negative_genre_data_filtered['Жанр негативного впливу'].value_counts().nlargest(5).reset_index(name='Кількість')
                title_negative_genre = 'Топ-5 жанрів негативного впливу (всі категорії)'
            else:
                genre_negative_category_data = negative_genre_data_filtered[negative_genre_data_filtered['Категорія негативного впливу'] == selected_genre_category2]
                genre_negative_counts = genre_negative_category_data['Жанр негативного впливу'].value_counts().nlargest(5).reset_index(name='Кількість')
                title_negative_genre = f'Топ-5 жанрів негативного впливу для категорії "{selected_genre_category2}"'

            genre_negative_counts.columns = ['Жанр', 'Кількість']

            fig_negative_genre = px.bar(genre_negative_counts, x='Кількість', y='Жанр', orientation='h',
                                            title=title_negative_genre, color_discrete_sequence=['#d62728'])
            fig_negative_genre.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=150, r=20, t=60, b=40),
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_negative_genre, use_container_width=True)
        else:
            st.error("Помилка: Відсутній стовпець 'Жанр негативного впливу'.")
        st.markdown('</div>', unsafe_allow_html=True)

    filtered_positive_genres = filtered_merged_df[
        (filtered_merged_df['Жанр позитивного впливу'] != 'Всі') & (filtered_merged_df['Жанр позитивного впливу'] != '0')
    ].copy()
    filtered_negative_genres = filtered_merged_df[
        (filtered_merged_df['Жанр негативного впливу'] != 'Всі') & (filtered_merged_df['Жанр негативного впливу'] != '0')
    ].copy()
#Четвертий ряд
    col1, col2 = st.columns([2, 1])
    with col1:
        positive_genre_type_counts = filtered_positive_genres.groupby(['Жанр позитивного впливу', 'Тип позитивного впливу']).size().unstack(fill_value=0)

        fig_heatmap_pos = px.imshow(positive_genre_type_counts,
                                    labels=dict(x="Тип позитивного впливу", y="Жанр позитивного впливу", color="Кількість"),
                                    color_continuous_scale="greens",
                                    text_auto=True,
                                    title="Теплова карта залежності типу позитивного впливу від жанру" ,
                                    aspect="auto")
        fig_heatmap_pos.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_heatmap_pos, use_container_width=True)
    # Топ-5 жанрів загального впливу
    with col2:
        positive_genre_counts = filtered_positive_genres['Жанр позитивного впливу'].value_counts().nlargest(5).reset_index(name='Позитивний вплив')
        negative_genre_counts = filtered_negative_genres['Жанр негативного впливу'].value_counts().nlargest(5).reset_index(name='Негативний вплив')
        top_genres_merged = pd.merge(positive_genre_counts, negative_genre_counts, left_on='Жанр позитивного впливу', right_on='Жанр негативного впливу', how='outer').fillna(0)
        top_genres_merged['Жанр'] = top_genres_merged['Жанр позитивного впливу'].fillna(top_genres_merged['Жанр негативного впливу'])
        top_genres_merged = top_genres_merged[['Жанр', 'Позитивний вплив', 'Негативний вплив']]
        top_genres_filtered = top_genres_merged[
            (top_genres_merged['Позитивний вплив'] > 0) | (top_genres_merged['Негативний вплив'] > 0)
        ].copy()
        top_genres_filtered['Загальний вплив'] = top_genres_filtered['Позитивний вплив'] + top_genres_filtered['Негативний вплив']
        top_5_genres_sorted = top_genres_filtered.sort_values(by='Загальний вплив', ascending=False).head(5)

        fig_stacked_genres = px.bar(top_5_genres_sorted,
                                    x='Жанр',
                                    y=['Позитивний вплив', 'Негативний вплив'],
                                    title="Топ-5 жанрів (стековано за впливом)",
                                    color_discrete_sequence=['#2ca02c', '#d62728'],
                                    labels={'value': 'Кількість згадувань', 'variable': 'Тип впливу'})
        fig_stacked_genres.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=True)
        st.plotly_chart(fig_stacked_genres, use_container_width=True)
    
#П'ятий ряд 
    col1, col2 = st.columns([2, 1])
    #Залежність типу негативного впливу від жанру 
    with col1:
        negative_genre_type_counts = filtered_negative_genres.groupby(['Жанр негативного впливу', 'Тип негативного впливу']).size().unstack(fill_value=0)

        fig_heatmap_neg = px.imshow(negative_genre_type_counts,
                                    labels=dict(x="Тип негативного впливу", y="Жанр негативного впливу", color="Кількість"),
                                    color_continuous_scale="orrd",
                                    title="Теплова карта залежності типу негативного впливу від жанру" ,
                                    text_auto=True,
                                    aspect="auto")
        fig_heatmap_neg.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_heatmap_neg, use_container_width=True)
    #Вплив часу гри 
    with col2:
        time_impact_df = filtered_merged_df[['Час', 'Позитивний вплив', 'Негативний вплив']].copy()
        time_mapping = {
            "менше 1 години": 0.5,
            "близько 1 години": 1,
            "близько 2 годин": 2,
            "близько 3 годин": 3,
            "4 години і більше": 4,
        }
        time_impact_df['Час_число'] = time_impact_df['Час'].map(time_mapping)
        time_impact_df['Позитивний вплив'] = time_impact_df['Позитивний вплив'].apply(lambda x: 1 if x == 'Так' else 0)
        time_impact_df['Негативний вплив'] = time_impact_df['Негативний вплив'].apply(lambda x: 1 if x == 'Так' else 0)
        grouped_by_time = time_impact_df.groupby('Час_число')[['Позитивний вплив', 'Негативний вплив']].sum()
        total_positive_tak = time_impact_df['Позитивний вплив'].sum()
        total_negative_tak = time_impact_df['Негативний вплив'].sum()
        normalized_impact = grouped_by_time.copy()
        normalized_impact['Позитивний вплив'] = normalized_impact['Позитивний вплив'] / total_positive_tak if total_positive_tak > 0 else 0
        normalized_impact['Негативний вплив'] = normalized_impact['Негативний вплив'] / total_negative_tak if total_negative_tak > 0 else 0
        normalized_impact = normalized_impact.reset_index()

        fig_time_impact= px.line(normalized_impact,
                                    x='Час_число',
                                    y=['Позитивний вплив', 'Негативний вплив'],
                                    labels={'Час_число': 'Час гри (години)', 'value': 'Частка від загальної кількості "Так"', 'variable': 'Тип впливу'},
                                    color_discrete_sequence=['#2ca02c', '#d62728'],
                                    title="Вплив часу гри" ,
                                    markers=True)
        fig_time_impact.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=True)
        st.plotly_chart(fig_time_impact, use_container_width=True)
