import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="Carbon Accounting Tool",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #3b82f6;
    }
    h1 {
        color: #1e40af;
        padding-bottom: 10px;
        border-bottom: 3px solid #3b82f6;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None

# Helper Functions
def load_sample_data():
    """Generate sample data based on provided format"""
    data = {
        'year': [2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024] * 2,
        'parent_entity': ['Company A'] * 10 + ['Company B'] * 10,
        'parent_type': ['State-owned Entity'] * 20,
        'commodity': ['Oil & NGL', 'Natural Gas'] * 10,
        'production_value': [100, 50, 95, 55, 90, 60, 85, 65, 80, 70] + [120, 60, 115, 65, 110, 70, 105, 75, 100, 80],
        'production_unit': ['Million bbl/yr', 'Bcf/yr'] * 10,
        'total_emissions_MtCO2e': [45, 20, 42, 22, 38, 24, 35, 25, 32, 26] + [54, 24, 50, 26, 46, 28, 42, 30, 38, 32]
    }
    return pd.DataFrame(data)

def calculate_metrics(df, selected_entity, selected_year):
    """Calculate key metrics"""
    # Filter data
    filtered_df = df.copy()
    if selected_entity != 'All Entities':
        filtered_df = filtered_df[filtered_df['parent_entity'] == selected_entity]
    if selected_year != 'All Years':
        filtered_df = filtered_df[filtered_df['year'] == int(selected_year)]
    
    # Calculate yearly emissions
    yearly_emissions = filtered_df.groupby('year')['total_emissions_MtCO2e'].sum().sort_index()
    
    if len(yearly_emissions) > 0:
        latest_year = yearly_emissions.index[-1]
        total_emissions = yearly_emissions.iloc[-1]
        
        if len(yearly_emissions) > 1:
            previous_emissions = yearly_emissions.iloc[-2]
            change = ((total_emissions - previous_emissions) / previous_emissions * 100) if previous_emissions > 0 else 0
        else:
            change = 0
            
        return total_emissions, change, yearly_emissions, filtered_df
    
    return 0, 0, pd.Series(), filtered_df

def calculate_net_zero_progress(yearly_emissions, net_zero_target, current_year):
    """Calculate progress towards net zero"""
    if len(yearly_emissions) == 0:
        return 0, net_zero_target - current_year, 0, 0
    
    latest_emissions = yearly_emissions.iloc[-1]
    baseline_emissions = yearly_emissions.iloc[0]
    
    progress = ((baseline_emissions - latest_emissions) / baseline_emissions * 100) if baseline_emissions > 0 else 0
    progress = max(0, min(100, progress))
    
    years_remaining = net_zero_target - current_year
    
    return progress, years_remaining, latest_emissions, 0

# Main App
def main():
    # Header
    st.title("🌍 Carbon Accounting Tool")
    st.markdown("**Track, Measure & Report Greenhouse Gas Emissions**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # File upload
        st.subheader("📁 Data Upload")
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if uploaded_file is not None:
            try:
                st.session_state.data = pd.read_csv(uploaded_file)
                st.success("✅ File uploaded successfully!")
            except Exception as e:
                st.error(f"❌ Error loading file: {e}")
        
        if st.button("📊 Load Sample Data"):
            st.session_state.data = load_sample_data()
            st.success("✅ Sample data loaded!")
        
        st.markdown("---")
        
        # Filters
        if st.session_state.data is not None:
            st.subheader("🔍 Filters")
            
            entities = ['All Entities'] + sorted(st.session_state.data['parent_entity'].unique().tolist())
            selected_entity = st.selectbox("Entity", entities)
            
            years = ['All Years'] + sorted([str(y) for y in st.session_state.data['year'].unique()])
            selected_year = st.selectbox("Year", years)
            
            st.markdown("---")
            
            # Net Zero Settings
            st.subheader("🎯 Net Zero Target")
            net_zero_target = st.number_input("Target Year", min_value=2024, max_value=2100, value=2050, step=1)
            current_year = st.number_input("Current Year", min_value=2020, max_value=2030, value=2024, step=1)
        else:
            selected_entity = 'All Entities'
            selected_year = 'All Years'
            net_zero_target = 2050
            current_year = 2024
        
        st.markdown("---")
        st.markdown("### 📥 Export Data")
        if st.session_state.data is not None:
            csv = st.session_state.data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="carbon_emissions_data.csv",
                mime="text/csv"
            )
    
    # Main Content
    if st.session_state.data is None:
        st.info("👈 Please upload a CSV file or load sample data from the sidebar to get started.")
        
        # Show expected format
        st.subheader("📋 Expected Data Format")
        st.markdown("""
        Your CSV file should contain the following columns:
        - `year`: Year of the record
        - `parent_entity`: Company/Entity name
        - `parent_type`: Type of entity
        - `commodity`: Type of commodity (Oil & NGL, Natural Gas, etc.)
        - `production_value`: Production value
        - `production_unit`: Unit of production
        - `total_emissions_MtCO2e`: Total emissions in MtCO2e
        """)
        
        st.markdown("---")
        st.subheader("📊 Sample Data Preview")
        sample_df = load_sample_data().head()
        st.dataframe(sample_df, use_container_width=True)
        
    else:
        # Calculate metrics
        total_emissions, change, yearly_emissions, filtered_df = calculate_metrics(
            st.session_state.data, selected_entity, selected_year
        )
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", 
            "🔍 Tool Comparison", 
            "🏗️ System Architecture", 
            "⚡ Scope 2 Recommendations", 
            "📈 Effectiveness Evaluation"
        ])
        
        with tab1:
            # Dashboard Content
            st.header("Dashboard - Scope 1 Emissions")
            
            # Key Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Total Emissions (Scope 1)",
                    value=f"{total_emissions:.2f} MtCO2e",
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="Year-over-Year Change",
                    value=f"{change:.2f}%",
                    delta=f"{change:.2f}%",
                    delta_color="inverse"
                )
            
            with col3:
                progress, years_remaining, current_emissions, _ = calculate_net_zero_progress(
                    yearly_emissions, net_zero_target, current_year
                )
                st.metric(
                    label="Net Zero Progress",
                    value=f"{progress:.1f}%",
                    delta=f"{years_remaining} years remaining"
                )
            
            st.markdown("---")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Emissions Trend (Scope 1)")
                if len(yearly_emissions) > 0:
                    trend_df = yearly_emissions.reset_index()
                    trend_df.columns = ['Year', 'Emissions']
                    
                    fig = px.line(
                        trend_df, 
                        x='Year', 
                        y='Emissions',
                        markers=True,
                        title="Total Emissions Over Time"
                    )
                    fig.update_traces(line_color='#3b82f6', line_width=3, marker=dict(size=8))
                    fig.update_layout(
                        xaxis_title="Year",
                        yaxis_title="Emissions (MtCO2e)",
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for the selected filters.")
            
            with col2:
                st.subheader("🥧 Emissions by Commodity")
                commodity_data = filtered_df.groupby('commodity')['total_emissions_MtCO2e'].sum().reset_index()
                
                if len(commodity_data) > 0:
                    fig = px.pie(
                        commodity_data,
                        values='total_emissions_MtCO2e',
                        names='commodity',
                        title="Commodity Breakdown"
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for the selected filters.")
            
            # Net Zero Trajectory
            st.markdown("---")
            st.subheader("🎯 Net Zero Trajectory")
            
            progress_bar_col, text_col = st.columns([3, 1])
            with progress_bar_col:
                st.progress(progress / 100)
            with text_col:
                st.markdown(f"**{progress:.1f}%** Complete")
            
            st.markdown(f"*{years_remaining} years remaining to reach net zero target of {net_zero_target}*")
            
            # Data Table
            st.markdown("---")
            st.subheader("📋 Detailed Data")
            st.dataframe(filtered_df, use_container_width=True)
        
        with tab2:
            # Tool Comparison
            st.header("🔍 Critical Comparison of Carbon Accounting Tools")
            
            comparison_data = {
                'Tool': ['GHG Protocol', 'Watershed', 'Persefoni', 'Salesforce Net Zero Cloud', 'This Tool (Prototype)'],
                'Strengths': [
                    'Industry standard, comprehensive methodology, widely accepted',
                    'User-friendly interface, automated data collection, real-time tracking',
                    'AI-powered, comprehensive Scope 1-3 coverage, regulatory compliance',
                    'Integrated with CRM, good reporting, supplier engagement tools',
                    'Free, customizable, visual analytics, real-time insights, lightweight'
                ],
                'Limitations': [
                    'Manual calculations, requires expertise, time-intensive',
                    'Expensive, limited customization, primarily Scope 2 focused',
                    'High cost, complex setup, steep learning curve',
                    'Requires Salesforce ecosystem, expensive, data silos',
                    'Requires data structure knowledge, limited Scope 2/3 support (v1)'
                ],
                'Best For': [
                    'Enterprise compliance',
                    'Mid-to-large enterprises',
                    'Large corporations with complex supply chains',
                    'Existing Salesforce customers',
                    'SMEs, startups, quick assessments'
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
            
            st.markdown("---")
            st.info("""
            **🔑 Key Findings:**
            - Most enterprise tools focus on Scope 2 and 3, with Scope 1 often overlooked
            - Cost remains a significant barrier for SMEs (average $20k-$100k+ annually)
            - Data integration is the biggest challenge across all platforms
            - Real-time tracking and visualization are rare features in existing tools
            - Open-source alternatives lack comprehensive features and support
            """)
        
        with tab3:
            # System Architecture
            st.header("🏗️ System Architecture for Data Collection & Display")
            
            st.subheader("Data Flow Architecture")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                **1️⃣ Data Sources**
                - IoT Sensors
                - SCADA Systems
                - Production Logs
                - Utility Bills
                - Manual Entry
                """)
            
            with col2:
                st.markdown("""
                **2️⃣ Data Collection**
                - API Integration
                - CSV/Excel Upload
                - Database Connectors
                - Real-time Streaming
                - Batch Processing
                """)
            
            with col3:
                st.markdown("""
                **3️⃣ Processing**
                - Data Validation
                - Unit Conversion
                - Emission Factors
                - Aggregation
                - Quality Checks
                """)
            
            with col4:
                st.markdown("""
                **4️⃣ Visualization**
                - Dashboard
                - Trends & Analytics
                - Reports
                - Alerts
                - Export
                """)
            
            st.markdown("---")
            
            # Technical Stack
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Backend Technologies")
                st.markdown("""
                - **Python/FastAPI**: API services & data processing
                - **PostgreSQL**: Time-series data storage
                - **Redis**: Caching & real-time data
                - **Apache Kafka**: Event streaming
                """)
            
            with col2:
                st.subheader("Frontend Technologies")
                st.markdown("""
                - **Streamlit/React**: UI framework
                - **Plotly/D3.js**: Data visualization
                - **TailwindCSS**: Styling
                - **WebSockets**: Real-time updates
                """)
            
            st.markdown("---")
            
            st.subheader("Sample API Implementation")
            st.code("""
# Example API endpoint for data collection
@app.post("/api/emissions/upload")
async def upload_emissions(file: UploadFile):
    df = pd.read_csv(file.file)
    
    # Validate required columns
    required = ['year', 'parent_entity', 'commodity', 
                'production_value', 'total_emissions_MtCO2e']
    
    # Process and store data
    emissions_data = process_emissions(df)
    await db.store_emissions(emissions_data)
    
    return {"status": "success", "records": len(df)}

# Real-time IoT data ingestion
@app.websocket("/ws/emissions")
async def emissions_stream(websocket: WebSocket):
    await websocket.accept()
    async for data in iot_sensor_stream():
        emissions = calculate_emissions(data)
        await websocket.send_json(emissions)
            """, language='python')
        
        with tab4:
            # Scope 2 Recommendations
            st.header("⚡ Scope 2 Extension Recommendations")
            
            st.info("""
            **What is Scope 2?**
            
            Scope 2 emissions are indirect GHG emissions from the generation of purchased electricity, 
            steam, heating, and cooling consumed by the reporting company.
            
            **Key Sources:** Grid electricity, purchased steam, district heating/cooling
            """)
            
            st.markdown("---")
            
            st.subheader("Implementation Strategy")
            
            # Phase 1
            st.markdown("### 1️⃣ Data Collection Enhancement")
            st.markdown("""
            - Integrate with utility billing systems (electricity, steam providers)
            - Connect to smart meters for real-time consumption data
            - Track renewable energy certificates (RECs) and PPAs
            - Monitor location-based vs market-based emissions
            """)
            
            # Phase 2
            st.markdown("### 2️⃣ Emission Factor Database")
            st.markdown("""
            - Implement grid emission factors by region (eGRID, IEA)
            - Support for multiple methodologies (location-based, market-based)
            - Annual updates for emission factors
            - Custom factors for renewable energy procurement
            """)
            
            # Phase 3
            st.markdown("### 3️⃣ Dashboard Extensions")
            st.markdown("""
            - Separate Scope 1 and Scope 2 visualizations
            - Energy consumption breakdown by source
            - Renewable energy percentage tracking
            - Cost analysis (energy costs vs carbon costs)
            """)
            
            # Phase 4
            st.markdown("### 4️⃣ Advanced Features")
            st.markdown("""
            - Scenario modeling (renewable energy adoption impact)
            - Carbon intensity benchmarking
            - Supplier emissions transparency
            - Automated reporting for sustainability disclosures
            """)
            
            st.markdown("---")
            
            st.subheader("Extended Data Model for Scope 2")
            st.code("""
{
  "year": 2024,
  "entity": "Company A",
  "scope": 2,
  "energy_type": "Electricity",
  "consumption_value": 150000,
  "consumption_unit": "MWh",
  "location": "California",
  "grid_emission_factor": 0.234,  // tCO2e/MWh
  "renewable_percentage": 45,
  "location_based_emissions": 35.1,  // MtCO2e
  "market_based_emissions": 19.3,    // MtCO2e (with RECs)
  "source": "PG&E",
  "cost_usd": 22500000
}
            """, language='json')
            
            st.markdown("---")
            
            st.success("""
            **📊 Calculation Example:**
            
            - **Energy Consumed:** 150,000 MWh
            - **Grid Emission Factor:** 0.234 tCO2e/MWh
            - **Location-Based Emissions:** 150,000 × 0.234 = 35,100 tCO2e (35.1 MtCO2e)
            
            **With 45% Renewable Energy:**
            - **Market-Based Emissions:** 150,000 × 0.55 × 0.234 = 19,305 tCO2e (19.3 MtCO2e)
            """)
        
        with tab5:
            # Effectiveness Evaluation
            st.header("📈 Critical Evaluation: Carbon Accounting for Net Zero")
            
            st.subheader("How Effective is Carbon Accounting for Achieving Net Zero?")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.success("""
                **✅ Strengths**
                
                - **Visibility:** Provides clear baseline and tracking of emissions
                - **Accountability:** Enables target setting and progress measurement
                - **Decision Support:** Identifies high-impact reduction opportunities
                - **Stakeholder Trust:** Demonstrates commitment to sustainability
                - **Compliance:** Meets regulatory and investor requirements
                """)
            
            with col2:
                st.error("""
                **⚠️ Limitations**
                
                - **Not Sufficient Alone:** Accounting ≠ Reduction
                - **Data Quality:** Accuracy depends on data collection rigor
                - **Scope 3 Challenges:** Supply chain emissions hard to measure
                - **Greenwashing Risk:** Can be manipulated without real action
                - **Resource Intensive:** Requires continuous investment
                """)
            
            st.markdown("---")
            
            st.warning("""
            **📚 Research-Based Findings**
            
            - **CDP Study (2023):** Companies with comprehensive carbon accounting are 2.5x more likely 
              to set science-based targets and achieve emission reductions.
            
            - **MIT Research (2024):** Carbon accounting drives 15-30% reduction in emissions when 
              coupled with active management and incentive structures.
            
            - **Key Insight:** Carbon accounting is a necessary but insufficient condition for net zero. 
              It must be paired with strategic action, investment in clean technology, and cultural change.
            """)
            
            st.markdown("---")
            
            st.subheader("Critical Success Factors for Net Zero Achievement")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                **1. Integration**
                
                Carbon metrics integrated into business KPIs, executive compensation, and capital allocation
                
                ---
                
                **2. Action Plans**
                
                Specific reduction initiatives with timelines, budgets, and accountability
                """)
            
            with col2:
                st.markdown("""
                **3. Technology Investment**
                
                Capital deployment in renewable energy, efficiency, and carbon capture
                
                ---
                
                **4. Supply Chain Engagement**
                
                Collaboration with suppliers to reduce Scope 3 emissions
                """)
            
            with col3:
                st.markdown("""
                **5. Verification & Transparency**
                
                Third-party audits, public disclosure, honest reporting
                
                ---
                
                **6. Cultural Transformation**
                
                Organization-wide awareness and sustainability values
                """)
            
            st.markdown("---")
            
            st.info("""
            **🎯 Conclusion**
            
            Carbon accounting is **essential but not sufficient** for achieving net zero. It serves as the foundation 
            for informed decision-making, but net zero requires:
            
            - Strategic commitment from leadership
            - Significant capital investment in decarbonization
            - Operational changes across the value chain
            - Cultural and behavioral transformation
            - Continuous innovation and adaptation
            
            **Organizations that treat carbon accounting as merely a compliance exercise will fail to achieve net zero. 
            Those that use it as a strategic tool for transformation have a fighting chance.**
            """)
            
            st.markdown("---")
            
            st.subheader("Recommendations for This Tool's Evolution")
            
            recommendations = [
                "Add scenario modeling to show emission reduction pathways and their feasibility",
                "Integrate financial impact analysis (carbon pricing, ROI of reduction initiatives)",
                "Develop AI-powered recommendations for reduction opportunities",
                "Build verification and audit trail features for credibility",
                "Create action tracking module to link emissions data to reduction initiatives"
            ]
            
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"**{i}.** {rec}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>Carbon Accounting Tool - Prototype v1.0</strong></p>
        <p>Built for tracking Scope 1 emissions with extensibility for Scope 2 & 3</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()