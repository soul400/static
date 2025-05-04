import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import re
from utils.api_handler import fetch_jaco_data, check_api_available
from utils.data_processor import process_stream_data, aggregate_data
from utils.scraper import scrape_jaco_data
from assets.help_text import HELP_TEXTS

# Set page configuration
st.set_page_config(
    page_title="إحصائيات بثوث المهره",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application states
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame({
        'timestamp': [],
        'stream_id': [],
        'streamer_name': [],
        'likes': [],
        'viewers': [],
        'comments': [],
        'gifts': []
    })

if 'selected_stream' not in st.session_state:
    st.session_state.selected_stream = None

if 'using_api' not in st.session_state:
    st.session_state.using_api = False

if 'using_scraper' not in st.session_state:
    st.session_state.using_scraper = False

if 'last_update' not in st.session_state:
    st.session_state.last_update = None

if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "غير متصل"

if 'update_frequency' not in st.session_state:
    st.session_state.update_frequency = 60  # seconds

def check_connection():
    """Check if Jaco.live API is available"""
    api_available = check_api_available()
    
    if api_available:
        st.session_state.using_api = True
        st.session_state.using_scraper = False
        st.session_state.connection_status = "متصل (API)"
        return True
    else:
        try:
            # Try scraping as fallback
            test_data = scrape_jaco_data("test")
            if test_data is not None:
                st.session_state.using_api = False
                st.session_state.using_scraper = True
                st.session_state.connection_status = "متصل (تحليل الويب)"
                return True
        except:
            st.session_state.using_api = False
            st.session_state.using_scraper = False
            st.session_state.connection_status = "غير متصل"
            return False
    
    return False

def update_data(stream_id):
    """Fetch updated data for the selected stream"""
    try:
        # Always use scraper regardless of connection status
        # This ensures we get data even if API check fails
        st.session_state.using_scraper = True
        new_data = scrape_jaco_data(stream_id)
        
        if new_data is not None:
            processed_data = process_stream_data(new_data, stream_id)
            
            # Print debug info
            print(f"Debug - Processed data: {processed_data}")
            
            # Add to existing data
            st.session_state.data = pd.concat([st.session_state.data, processed_data])
            st.session_state.last_update = datetime.now()
            
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحديث البيانات: {str(e)}")

def add_manual_data():
    """Add manually entered data to the dataset"""
    with st.form("manual_data_form"):
        col1, col2 = st.columns(2)
        with col1:
            stream_id = st.text_input("معرف البث", value=st.session_state.selected_stream if st.session_state.selected_stream else "")
            streamer_name = st.text_input("اسم المبث")
            likes = st.number_input("عدد الإعجابات", min_value=0, value=0)
        
        with col2:
            viewers = st.number_input("عدد المشاهدين", min_value=0, value=0)
            comments = st.number_input("عدد التعليقات", min_value=0, value=0)
            gifts = st.number_input("عدد الهدايا", min_value=0, value=0)
        
        submitted = st.form_submit_button("إضافة البيانات")
        
        if submitted:
            # Create new data entry
            new_entry = pd.DataFrame({
                'timestamp': [datetime.now()],
                'stream_id': [stream_id],
                'streamer_name': [streamer_name],
                'likes': [likes],
                'viewers': [viewers],
                'comments': [comments],
                'gifts': [gifts]
            })
            
            # Add to existing data
            st.session_state.data = pd.concat([st.session_state.data, new_entry])
            st.session_state.selected_stream = stream_id
            st.session_state.last_update = datetime.now()
            st.success("تمت إضافة البيانات بنجاح!")

def create_dashboard():
    """Create the main dashboard with visualizations"""
    if st.session_state.data.empty or st.session_state.selected_stream is None:
        return
        
    # Filter data for the selected stream
    stream_data = st.session_state.data[st.session_state.data['stream_id'] == st.session_state.selected_stream].copy()
    
    if stream_data.empty:
        st.warning("لا توجد بيانات متاحة للبث المحدد")
        return
    
    # Sort by timestamp for proper trend visualization
    stream_data = stream_data.sort_values('timestamp')
    
    # Convert timestamp to more readable format for display
    stream_data['time_display'] = stream_data['timestamp'].dt.strftime('%H:%M:%S')
    
    # Get the most recent data point
    latest_data = stream_data.iloc[-1]
    streamer_name = latest_data['streamer_name']
    
    # Display header with streamer info
    st.header(f"لوحة إحصائيات بث {streamer_name} ({st.session_state.selected_stream})")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("الإعجابات", f"{int(latest_data['likes']):,}", 
                  delta=int(latest_data['likes'] - stream_data['likes'].iloc[-2]) if len(stream_data) > 1 else None)
    with col2:
        st.metric("المشاهدون", f"{int(latest_data['viewers']):,}", 
                  delta=int(latest_data['viewers'] - stream_data['viewers'].iloc[-2]) if len(stream_data) > 1 else None)
    with col3:
        st.metric("التعليقات", f"{int(latest_data['comments']):,}", 
                  delta=int(latest_data['comments'] - stream_data['comments'].iloc[-2]) if len(stream_data) > 1 else None)
    with col4:
        st.metric("الهدايا", f"{int(latest_data['gifts']):,}", 
                  delta=int(latest_data['gifts'] - stream_data['gifts'].iloc[-2]) if len(stream_data) > 1 else None)
    
    # Charts
    st.subheader("تطور الإحصائيات خلال البث")
    
    tab1, tab2, tab3 = st.tabs(["معدلات التفاعل", "عدد المشاهدين", "الهدايا والتعليقات"])
    
    with tab1:
        engagement_fig = px.line(stream_data, x='time_display', y=['likes', 'comments'], 
                              title="تطور الإعجابات والتعليقات مع الوقت",
                              labels={"time_display": "الوقت", "value": "العدد", "variable": "النوع"})
        engagement_fig.update_layout(
            xaxis_title="الوقت",
            yaxis_title="العدد",
            legend_title="النوع",
            hovermode="x",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(engagement_fig, use_container_width=True)
        
    with tab2:
        viewers_fig = px.area(stream_data, x='time_display', y='viewers', 
                           title="تطور عدد المشاهدين مع الوقت",
                           labels={"time_display": "الوقت", "viewers": "عدد المشاهدين"})
        viewers_fig.update_layout(
            xaxis_title="الوقت",
            yaxis_title="عدد المشاهدين",
            hovermode="x"
        )
        st.plotly_chart(viewers_fig, use_container_width=True)
        
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            comments_per_minute = []
            for i in range(1, len(stream_data)):
                time_diff = (stream_data['timestamp'].iloc[i] - stream_data['timestamp'].iloc[i-1]).total_seconds() / 60
                comment_diff = stream_data['comments'].iloc[i] - stream_data['comments'].iloc[i-1]
                if time_diff > 0:
                    comments_per_minute.append(comment_diff / time_diff)
                else:
                    comments_per_minute.append(0)
            
            # Add 0 for the first point to match length
            comments_per_minute = [0] + comments_per_minute
            stream_data['comments_per_minute'] = comments_per_minute
            
            comments_fig = px.bar(stream_data, x='time_display', y='comments_per_minute',
                               title="معدل التعليقات لكل دقيقة",
                               labels={"time_display": "الوقت", "comments_per_minute": "التعليقات/دقيقة"})
            comments_fig.update_layout(
                xaxis_title="الوقت",
                yaxis_title="التعليقات/دقيقة"
            )
            st.plotly_chart(comments_fig, use_container_width=True)
        
        with col2:
            gifts_fig = px.line(stream_data, x='time_display', y='gifts',
                             title="تطور عدد الهدايا مع الوقت",
                             labels={"time_display": "الوقت", "gifts": "عدد الهدايا"})
            gifts_fig.update_layout(
                xaxis_title="الوقت",
                yaxis_title="عدد الهدايا"
            )
            st.plotly_chart(gifts_fig, use_container_width=True)
    
    # Overall stream statistics
    st.subheader("إحصائيات عامة للبث")
    
    # Calculate metrics
    stream_duration = (stream_data['timestamp'].max() - stream_data['timestamp'].min()).total_seconds() / 60
    total_likes = int(latest_data['likes'])
    total_comments = int(latest_data['comments'])
    total_gifts = int(latest_data['gifts'])
    max_viewers = int(stream_data['viewers'].max())
    avg_viewers = int(stream_data['viewers'].mean())
    
    # Display metrics in a nice format
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"⏱️ مدة البث: {stream_duration:.1f} دقيقة")
        st.info(f"👍 إجمالي الإعجابات: {total_likes:,}")
    with col2:
        st.info(f"👥 أقصى عدد مشاهدين: {max_viewers:,}")
        st.info(f"👥 متوسط المشاهدين: {avg_viewers:,}")
    with col3:
        st.info(f"💬 إجمالي التعليقات: {total_comments:,}")
        st.info(f"🎁 إجمالي الهدايا: {total_gifts:,}")
    
    # Last update time
    if st.session_state.last_update:
        st.caption(f"آخر تحديث: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    # Sidebar
    with st.sidebar:
        st.title("إحصائيات بثوث المهره")
        # Remove placeholder image as requested by user
        
        # Connection status
        st.subheader("حالة الاتصال")
        conn_col1, conn_col2 = st.columns([3, 1])
        
        with conn_col1:
            st.write(f"الحالة: {st.session_state.connection_status}")
        
        with conn_col2:
            if st.button("فحص"):
                with st.spinner("جاري الفحص..."):
                    connected = check_connection()
                    if connected:
                        st.success("تم الاتصال بنجاح")
                    else:
                        st.error("فشل الاتصال")
        
        # Stream selection
        st.subheader("اختيار البث")
        
        st.markdown("""
        **كيفية الاستخدام:**
        - يمكنك لصق رابط البث مباشرة من Jaco.live (مثال: https://jaco.live/username/stream123)
        - أو يمكنك إدخال معرف البث فقط (مثال: username/stream123)
        """)
        
        stream_url = st.text_input("أدخل رابط البث أو معرف البث", 
                                 value=st.session_state.selected_stream if st.session_state.selected_stream else "",
                                 help="يمكنك نسخ الرابط من المتصفح ولصقه هنا")
        
        # Extract stream ID from URL if necessary
        if stream_url:
            # Try to extract stream ID from full URL
            url_match = re.search(r'jaco\.live/([^/]+(?:/[^/]+)?)', stream_url)
            if url_match:
                stream_id = url_match.group(1)
            else:
                # If it's not a URL, use as is
                stream_id = stream_url
        else:
            stream_id = ""
            
        # Show extracted ID
        if stream_id and stream_id != stream_url:
            st.success(f"تم استخراج معرف البث: {stream_id}")
        
        if st.button("تتبع البث"):
            if stream_id:
                st.session_state.selected_stream = stream_id
                with st.spinner("جاري تحميل بيانات البث..."):
                    update_data(stream_id)
                st.success(f"تم اختيار البث: {stream_id}")
            else:
                st.error("يرجى إدخال رابط البث أو معرف البث")
        
        # Update frequency
        st.subheader("إعدادات التحديث")
        update_freq = st.slider("الفاصل الزمني للتحديث (ثانية)", 
                               min_value=10, max_value=300, value=st.session_state.update_frequency, step=10)
        
        if update_freq != st.session_state.update_frequency:
            st.session_state.update_frequency = update_freq
            st.success(f"تم تغيير فترة التحديث إلى {update_freq} ثانية")
        
        # Export data
        st.subheader("تصدير البيانات")
        if not st.session_state.data.empty and st.session_state.selected_stream:
            stream_data = st.session_state.data[st.session_state.data['stream_id'] == st.session_state.selected_stream]
            if not stream_data.empty:
                csv_data = stream_data.to_csv(index=False)
                st.download_button(
                    label="تنزيل البيانات (CSV)",
                    data=csv_data,
                    file_name=f"jaco_stream_{st.session_state.selected_stream}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        # Help section
        with st.expander("مساعدة"):
            st.write(HELP_TEXTS['main_help'])
    
    # Main content
    st.title("📊 إحصائيات بثوث المهره")
    
    # Simplified header with no images as requested by user
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["لوحة المعلومات", "إدخال البيانات", "حول التطبيق"])
    
    with tab1:
        if not st.session_state.data.empty and st.session_state.selected_stream:
            # Check if it's time to update data
            if (st.session_state.last_update is None or 
                (datetime.now() - st.session_state.last_update).total_seconds() >= st.session_state.update_frequency):
                with st.spinner("جاري تحديث البيانات..."):
                    update_data(st.session_state.selected_stream)
            
            # Create and display dashboard
            create_dashboard()
            
            # Auto-refresh option
            auto_refresh = st.checkbox("تحديث تلقائي", value=True)
            if auto_refresh:
                time_to_refresh = st.session_state.update_frequency
                if st.session_state.last_update:
                    elapsed = (datetime.now() - st.session_state.last_update).total_seconds()
                    time_to_refresh = max(1, st.session_state.update_frequency - elapsed)
                
                st.write(f"سيتم التحديث تلقائيًا بعد {int(time_to_refresh)} ثانية")
                time.sleep(min(10, time_to_refresh))  # Sleep for a maximum of 10 seconds to prevent UI freezing
                st.rerun()
        else:
            # No data yet, show welcome screen
            st.info("مرحبًا بك في تطبيق إحصائيات بثوث المهره!")
            st.write("لبدء تتبع بث، يرجى إدخال معرف البث في الشريط الجانبي ثم الضغط على 'تتبع البث'.")
            
            # Simple welcome message with no images
            st.info("قم بإدخال رابط البث أو معرف البث في الشريط الجانبي واضغط زر 'تتبع البث' لبدء جمع الإحصائيات")
    
    with tab2:
        st.header("إدخال البيانات يدويًا")
        st.write("استخدم هذا القسم لإدخال بيانات البث يدويًا في حال عدم توفر اتصال مباشر مع المنصة.")
        
        add_manual_data()
    
    with tab3:
        st.header("حول التطبيق")
        
        st.subheader("إحصائيات بثوث المهره")
        st.write("""
        هذا التطبيق يساعدك على تتبع وتحليل إحصائيات البث المباشر من منصة Jaco.live بطريقة سهلة وبسيطة.
        
        يمكنك من خلاله:
        - تتبع عدد الإعجابات والمشاهدين والتعليقات والهدايا
        - مشاهدة تطور الإحصائيات في الوقت الفعلي
        - تحليل أداء البث من خلال الرسوم البيانية
        - تصدير البيانات للاستخدام في برامج أخرى
        
        للاستخدام الأمثل، أدخل معرف البث واترك التطبيق يعمل على جمع وتحليل البيانات تلقائيًا.
        """)
        
        st.subheader("كيفية الاستخدام")
        st.markdown(HELP_TEXTS['how_to_use'])

if __name__ == "__main__":
    main()
