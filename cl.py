import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Stock Movement Analysis Dashboard", layout="wide")

st.title("📊 Stock Movement Analysis Dashboard")

# File uploaders
st.sidebar.header("Upload Files")

qwtt_inventory_file = st.sidebar.file_uploader("QWTT Inventory (Excel/CSV)", type=['xlsx', 'csv'])
amazon_stock_file = st.sidebar.file_uploader("Amazon Stock (CSV)", type=['csv'])
flipkart_business_file = st.sidebar.file_uploader("Flipkart Business Report (Excel)", type=['xlsx'])
amazon_business_file = st.sidebar.file_uploader(
    "Amazon Business Report (Excel/CSV)", 
    type=['xlsx', 'csv']
)
amazon_pm_file = st.sidebar.file_uploader("Amazon PM (Excel)", type=['xlsx'])
flipkart_pm_file = st.sidebar.file_uploader("Flipkart PM (Excel)", type=['xlsx'])
flipkart_inventory_file = st.sidebar.file_uploader("Flipkart Easycom Inventory (CSV)", type=['csv'])

if all([qwtt_inventory_file, amazon_stock_file, flipkart_business_file, 
        amazon_business_file, amazon_pm_file, flipkart_pm_file, flipkart_inventory_file]):
    
    with st.spinner("Processing data..."):
        # Load data
        if qwtt_inventory_file.name.endswith('.csv'):
            Qwtt_Inventory = pd.read_csv(qwtt_inventory_file)
        else:
            Qwtt_Inventory = pd.read_excel(qwtt_inventory_file)
        Amazon_Stock = pd.read_csv(amazon_stock_file)
        Flipkart_Business_Report = pd.read_excel(flipkart_business_file)
        # Try to read the specific sheet for Amazon Business Report if it exists
        # Load Amazon Business Report (Excel or CSV)
        if amazon_business_file.name.endswith('.csv'):
            Amazon_Business_Report = pd.read_csv(amazon_business_file)
        else:
            try:
                Amazon_Business_Report = pd.read_excel(
                    amazon_business_file, 
                    sheet_name='BusinessReport-AMAZON'
                )
            except:
                Amazon_Business_Report = pd.read_excel(amazon_business_file)

                
        Amazon_PM = pd.read_excel(amazon_pm_file)
        Flipkart_PM = pd.read_excel(flipkart_pm_file)
        Flipkart_Easycom_Inventory = pd.read_csv(flipkart_inventory_file)
        
        Qwtt_Inventory["Sellable"] = (
            Qwtt_Inventory["Sellable"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        Qwtt_Inventory["Sellable"] = pd.to_numeric(
            Qwtt_Inventory["Sellable"], errors="coerce"
        ).fillna(0)

        # Process QWTT Inventory
        Qwtt_Inventory_Pivot = (
            Qwtt_Inventory
            .pivot_table(index="Asin", values="Sellable", aggfunc="sum")
            .reset_index()
            .sort_values(by="Sellable", ascending=False)
        )
        
        # Process Amazon Stock
        Amazon_Stock["afn-warehouse-quantity"] = (
            Amazon_Stock["afn-warehouse-quantity"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        Amazon_Stock["afn-warehouse-quantity"] = pd.to_numeric(
            Amazon_Stock["afn-warehouse-quantity"], errors="coerce"
        ).fillna(0)

        amazon_stock_pivot = (
            Amazon_Stock
            .pivot_table(index="asin", values="afn-warehouse-quantity", aggfunc="sum")
            .reset_index()
        )
        
        # Process Flipkart Business Report
        Flipkart_Business_Report["Final Sale Units"] = (
            Flipkart_Business_Report["Final Sale Units"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        Flipkart_Business_Report["Final Sale Units"] = pd.to_numeric(
            Flipkart_Business_Report["Final Sale Units"], errors="coerce"
        ).fillna(0)

        Flipkart_Business_Report.loc[
            Flipkart_Business_Report["Final Sale Units"] < 0,
            "Final Sale Units"
        ] = 0

        # =============================
        # FLIPKART SALES TRUTH PIVOT
        # =============================

        flipkart_sales_pivot = (
            Flipkart_Business_Report
            .pivot_table(
                index="Product Id",
                values="Final Sale Units",
                aggfunc="sum"
            )
            .reset_index()
        )

        # SAVE CORRECT TOTALS (VERY IMPORTANT)
        flipkart_total_sale_units_truth = int(flipkart_sales_pivot["Final Sale Units"].sum())
        flipkart_total_products_truth = len(flipkart_sales_pivot)

        
        # Flipkart_Business_Pivot = (
        #     Flipkart_Business_Report
        #     .pivot_table(index="Product Id", values="Final Sale Units", aggfunc="sum")
        #     .reset_index()
        # )
        
        # Process Amazon Business Report
        # Ensure numeric columns (handles CSV + Excel safely)
        Amazon_Business_Report["Total Order Items"] = (
            Amazon_Business_Report["Total Order Items"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        Amazon_Business_Report["Total Order Items"] = pd.to_numeric(
            Amazon_Business_Report["Total Order Items"], errors="coerce"
        ).fillna(0)


        Amazon_Business_Report["Total Order Items - B2B"] = (
            Amazon_Business_Report["Total Order Items - B2B"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        Amazon_Business_Report["Total Order Items - B2B"] = pd.to_numeric(
            Amazon_Business_Report["Total Order Items - B2B"], errors="coerce"
        ).fillna(0)


        Amazon_Business_Report["Total Orders"] = (
            Amazon_Business_Report["Total Order Items"] +
            Amazon_Business_Report["Total Order Items - B2B"]
        )
        
        # =========================
        # AMAZON SALES TRUTH PIVOT
        # =========================

        amazon_sales_pivot = (
            Amazon_Business_Report
            .pivot_table(
                index="(Parent) ASIN",
                values="Total Orders",
                aggfunc="sum"
            )
            .reset_index()
        )

        # SAVE CORRECT TOTALS (VERY IMPORTANT)
        amazon_total_orders_truth = int(amazon_sales_pivot["Total Orders"].sum())
        amazon_total_products_truth = len(amazon_sales_pivot)

        # this pivot doesn't give correct input 
        # amazon_business_pivot = (
        #     Amazon_Business_Report
        #     .pivot_table(index="(Parent) ASIN", values="Total Orders", aggfunc="sum")
        #     .reset_index()
        #     .sort_values(by="Total Orders", ascending=False)
        # )
        
        # Clean and standardize columns
        Amazon_PM["ASIN"] = Amazon_PM["ASIN"].astype(str).str.strip().str.upper()
        Amazon_PM["Vendor SKU Codes"] = Amazon_PM["Vendor SKU Codes"].astype(str).str.strip()
        Amazon_PM["EasycomSKU"] = Amazon_PM["EasycomSKU"].astype(str).str.strip()
        
        # Remove duplicates from Amazon PM to prevent expansion during merge
        # Priority sort: Rows with EasycomSKU and CP come first
        Amazon_PM["EasycomSKU_Clean"] = Amazon_PM["EasycomSKU"].astype(str).replace(["nan", ""], pd.NA)
        Amazon_PM = (
            Amazon_PM.sort_values(by=["EasycomSKU_Clean", "CP"], na_position='last', ascending=[True, False])
            .drop_duplicates(subset=['ASIN'])
            .drop(columns=["EasycomSKU_Clean"])
        )
        
        amazon_sales_pivot["(Parent) ASIN"] = (
            amazon_sales_pivot["(Parent) ASIN"].astype(str).str.strip().str.upper()
        )
        amazon_sales_pivot.columns = amazon_sales_pivot.columns.str.strip()
        
        # Ensure numeric CP and Total Orders
        Amazon_PM["CP"] = (
            Amazon_PM["CP"]
            .astype(str)
            .str.replace("₹", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.replace("--", "", regex=False)
            .str.strip()
        )

        Amazon_PM["CP"] = pd.to_numeric(
            Amazon_PM["CP"], errors="coerce"
        ).fillna(0)
        
        # Merge Amazon Business with PM
        
        amazon_business_pivot = amazon_sales_pivot.merge(
            Amazon_PM[[
                "ASIN", "Brand", "Brand Manager", "Product Name",
                "Vendor SKU Codes", "EasycomSKU", "CP"
            ]],
            left_on="(Parent) ASIN",
            right_on="ASIN",
            how="left"
        )

        # amazon_business_pivot = amazon_business_pivot.merge(
        #     Amazon_PM[["ASIN", "Brand", "Brand Manager", "Product Name", 
        #               "Vendor SKU Codes", "EasycomSKU", "CP"]],
        #     left_on="(Parent) ASIN",
        #     right_on="ASIN",
        #     how="left"
        # )
        
        amazon_business_pivot = amazon_business_pivot[[
            "(Parent) ASIN", "Brand", "Brand Manager", "Product Name",
            "Vendor SKU Codes", "EasycomSKU", "Total Orders", "CP"
        ]]

        # Clean "nan" strings and set actual NaNs for better sorting
        amazon_business_pivot["EasycomSKU"] = amazon_business_pivot["EasycomSKU"].replace(["nan", ""], pd.NA)
        
        # Sort to prioritize rows with EasycomSKU and then drop duplicates by ASIN
        # This keeps unmapped items but prefers the mapped version if duplicates exist
        # amazon_business_pivot = (
        #     amazon_business_pivot.sort_values(by="EasycomSKU", na_position='last')
        #     .drop_duplicates(subset=["(Parent) ASIN"])
        # )


        # amazon_business_pivot["Total Orders"] = pd.to_numeric(
        #     amazon_business_pivot["Total Orders"], 
        #     errors="coerce"
        # ).fillna(0)

        amazon_business_pivot["CP As Per Qty"] = (
            amazon_business_pivot["CP"] * amazon_business_pivot["Total Orders"]
        )

        # Add QWTT Stock to Amazon
        Qwtt_Inventory_Pivot["Asin"] = (
            Qwtt_Inventory_Pivot["Asin"].astype(str).str.strip().str.upper()
        )
        qwtt_stock_map = Qwtt_Inventory_Pivot.set_index("Asin")["Sellable"]
        amazon_business_pivot["QWTT Stock"] = (
            amazon_business_pivot["(Parent) ASIN"]
            .map(qwtt_stock_map)
            .fillna(0)
            .astype(int)
        )
        
        # Process Flipkart PM
        Flipkart_PM.columns = Flipkart_PM.columns.str.strip()
        Flipkart_PM["FNS"] = Flipkart_PM["FNS"].astype(str).str.strip().str.upper()
        Flipkart_PM["EasycomSKU"] = Flipkart_PM["EasycomSKU"].astype(str).str.strip()
        
        # Remove duplicates from Flipkart PM
        # Priority sort: Rows with EasycomSKU and CP come first
        Flipkart_PM["EasycomSKU_Clean"] = Flipkart_PM["EasycomSKU"].astype(str).replace(["nan", ""], pd.NA)
        Flipkart_PM = (
            Flipkart_PM.sort_values(by=["EasycomSKU_Clean", "CP"], na_position='last', ascending=[True, False])
            .drop_duplicates(subset=['FNS'])
            .drop(columns=["EasycomSKU_Clean"])
        )
        
        flipkart_sales_pivot.columns = flipkart_sales_pivot.columns.str.strip()
        flipkart_sales_pivot["Product Id"] = flipkart_sales_pivot["Product Id"].astype(str).str.strip().str.upper()
        
        Flipkart_Business_Pivot = flipkart_sales_pivot.merge(
            Flipkart_PM[[
                "FNS", "Brand", "Brand Manager", "Product Name",
                "Vendor SKU Codes", "EasycomSKU", "CP"
            ]],
            left_on="Product Id",
            right_on="FNS",
            how="left"
        )
        
        # Flipkart_Business_Pivot = Flipkart_Business_Pivot.merge(
        #     Flipkart_PM[["FNS", "Brand", "Brand Manager", "Product Name",
        #                 "Vendor SKU Codes", "EasycomSKU", "CP"]],
        #     left_on="Product Id",
        #     right_on="FNS",
        #     how="left"
        # )
        
        Flipkart_Business_Pivot = Flipkart_Business_Pivot[[
            "Product Id", "Brand", "Brand Manager", "Product Name",
            "Vendor SKU Codes", "EasycomSKU", "Final Sale Units", "CP", "FNS"
        ]]
        
        # Clean "nan" strings and set actual NaNs
        Flipkart_Business_Pivot["EasycomSKU"] = Flipkart_Business_Pivot["EasycomSKU"].replace(["nan", ""], pd.NA)
        
        # Sort to prioritize rows with EasycomSKU and drop duplicates by Product Id
        Flipkart_Business_Pivot = (
            Flipkart_Business_Pivot.sort_values(by="EasycomSKU", na_position='last')
            .drop_duplicates(subset=["Product Id"])
        )
        
        # Flipkart_Business_Pivot["CP As Per Qty"] = (
        #     Flipkart_Business_Pivot["CP"] * Flipkart_Business_Pivot["Final Sale Units"]
        # )
        Flipkart_Business_Pivot["CP"] = (
            Flipkart_Business_Pivot["CP"]
            .astype(str)
            .str.replace("₹", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        Flipkart_Business_Pivot["CP"] = pd.to_numeric(
            Flipkart_Business_Pivot["CP"], errors="coerce"
        ).fillna(0)

        Flipkart_Business_Pivot["Final Sale Units"] = pd.to_numeric(
            Flipkart_Business_Pivot["Final Sale Units"], errors="coerce"
        ).fillna(0)

        Flipkart_Business_Pivot["CP As Per Qty"] = (
            Flipkart_Business_Pivot["CP"] * Flipkart_Business_Pivot["Final Sale Units"]
        )
        
        # Add Flipkart QWTT Stock
        
        Flipkart_Easycom_Inventory["old_quantity"] = (
            Flipkart_Easycom_Inventory["old_quantity"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        Flipkart_Easycom_Inventory["old_quantity"] = pd.to_numeric(
            Flipkart_Easycom_Inventory["old_quantity"], errors="coerce"
        ).fillna(0)

        Flipkart_Easycom_Inventory["sku"] = (
            Flipkart_Easycom_Inventory["sku"].str.replace(r"^`", "", regex=True)
        )
        
        flipkart_inventory_pivot = (
            Flipkart_Easycom_Inventory
            .pivot_table(index="sku", values="old_quantity", aggfunc="sum")
            .reset_index()
        )
        
        flipkart_stock_map = flipkart_inventory_pivot.set_index("sku")["old_quantity"]
        Flipkart_Business_Pivot["QWTT Stock"] = (
            Flipkart_Business_Pivot["EasycomSKU"].map(flipkart_stock_map)
        )
        
        # Create Flipkart QWTT Inward
        flipkart_qwtt_inward = amazon_business_pivot.copy()
        
        flipkart_sales_map = (
            Flipkart_Business_Pivot
            .groupby("EasycomSKU")["Final Sale Units"]
            .sum()
        )
        flipkart_qwtt_inward["Flipkart Sales"] = (
            flipkart_qwtt_inward["EasycomSKU"]
            .map(flipkart_sales_map)
            .fillna(0)
            .astype(int)
        )
        
        flipkart_stock_map_inward = (
            Flipkart_Business_Pivot
            .groupby("EasycomSKU")["QWTT Stock"]
            .sum()
        )
        flipkart_qwtt_inward["Flipkart QWTT Stock"] = (
            flipkart_qwtt_inward["EasycomSKU"]
            .map(flipkart_stock_map_inward)
            .fillna(0)
            .astype(int)
        )
        
        flipkart_fns_map = (
            Flipkart_Business_Pivot
            .groupby("EasycomSKU")["FNS"]
            .first()
        )

        flipkart_qwtt_inward["FNS"] = (
            flipkart_qwtt_inward["EasycomSKU"].map(flipkart_fns_map)
        )
        
        flipkart_qwtt_inward_filter = flipkart_qwtt_inward[
            flipkart_qwtt_inward["Flipkart QWTT Stock"] == 0
        ].reset_index(drop=True)
        
        # Create Amazon QWTT Inward
        amazon_qwtt_inward = Flipkart_Business_Pivot.copy()
        
        amazon_sales_map = (
            amazon_business_pivot
            .groupby("EasycomSKU")["Total Orders"]
            .sum()
        )
        amazon_qwtt_inward["Amazon Sales"] = (
            amazon_qwtt_inward["EasycomSKU"]
            .map(amazon_sales_map)
            .fillna(0)
            .astype(int)
        )
        
        amazon_stock_map = (
            amazon_business_pivot
            .groupby("EasycomSKU")["QWTT Stock"]
            .sum()
        )
        amazon_qwtt_inward["Amazon Stock"] = (
            amazon_qwtt_inward["EasycomSKU"]
            .map(amazon_stock_map)
            .fillna(0)
            .astype(int)
        )
        
        amazon_asin_map = (
            amazon_business_pivot
            .groupby("EasycomSKU")["(Parent) ASIN"]
            .first()
        )

        amazon_qwtt_inward["Amazon ASIN"] = (
            amazon_qwtt_inward["EasycomSKU"].map(amazon_asin_map)
        )
        
        amazon_qwtt_inward_filter = amazon_qwtt_inward[
            amazon_qwtt_inward["Amazon Stock"] == 0
        ].reset_index(drop=True)
    
    # Display tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Amazon Business Pivot",
        "Flipkart Business Pivot",
        "Flipkart QWTT Inward",
        "Amazon QWTT Inward"
    ])
    
    with tab1:
        st.header("Amazon Business Pivot")
        st.dataframe(amazon_business_pivot, use_container_width=True, height=600)
        st.write("TABLE Total Orders:", amazon_business_pivot["Total Orders"].sum())
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Products", amazon_total_products_truth)
            st.metric("Total Orders", f"{amazon_total_orders_truth:,}")

            # st.metric("Total Products", len(amazon_business_pivot))
            # st.metric("Total Orders", f"{amazon_business_pivot['Total Orders'].sum():,.0f}")
        with col2:
            st.metric("Total CP Value", f"₹{amazon_business_pivot['CP As Per Qty'].sum():,.2f}")
            st.metric("Total QWTT Stock", f"{amazon_business_pivot['QWTT Stock'].sum():,.0f}")
        
        # Download button
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            amazon_business_pivot.to_excel(writer, index=False)
        st.download_button(
            label="📥 Download Excel",
            data=buffer.getvalue(),
            file_name="amazon_business_pivot.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with tab2:
        st.header("Flipkart Business Pivot")
        st.dataframe(Flipkart_Business_Pivot, use_container_width=True, height=600)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Products", flipkart_total_products_truth)
            st.metric("Total Sale Units", f"{flipkart_total_sale_units_truth:,}")
            # st.metric("Total Products", len(Flipkart_Business_Pivot))
            # st.metric("Total Sale Units", f"{Flipkart_Business_Pivot['Final Sale Units'].sum():,.0f}")
        with col2:
            st.metric("Total CP Value", f"₹{Flipkart_Business_Pivot['CP As Per Qty'].sum():,.2f}")
            st.metric("Total QWTT Stock", f"{Flipkart_Business_Pivot['QWTT Stock'].sum():,.0f}")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            Flipkart_Business_Pivot.to_excel(writer, index=False)
        st.download_button(
            label="📥 Download Excel",
            data=buffer.getvalue(),
            file_name="flipkart_business_pivot.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with tab3:
        st.header("Flipkart QWTT Inward")
        
        show_filter = st.checkbox("Show only products with zero Flipkart QWTT Stock", value=False)
        
        if show_filter:
            st.dataframe(flipkart_qwtt_inward_filter, use_container_width=True, height=600)
            data_to_show = flipkart_qwtt_inward_filter
        else:
            st.dataframe(flipkart_qwtt_inward, use_container_width=True, height=600)
            data_to_show = flipkart_qwtt_inward
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Products", len(data_to_show))
            st.metric("Total Amazon Orders", f"{data_to_show['Total Orders'].sum():,.0f}")
        with col2:
            st.metric("Total Flipkart Sales", f"{data_to_show['Flipkart Sales'].sum():,.0f}")
            st.metric("Total Flipkart QWTT Stock", f"{data_to_show['Flipkart QWTT Stock'].sum():,.0f}")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            data_to_show.to_excel(writer, index=False)
        st.download_button(
            label="📥 Download Excel",
            data=buffer.getvalue(),
            file_name="flipkart_qwtt_inward.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with tab4:
        st.header("Amazon QWTT Inward")
        
        show_filter = st.checkbox("Show only products with zero Amazon Stock", value=False, key="amazon_filter")
        
        if show_filter:
            st.dataframe(amazon_qwtt_inward_filter, use_container_width=True, height=600)
            data_to_show = amazon_qwtt_inward_filter
        else:
            st.dataframe(amazon_qwtt_inward, use_container_width=True, height=600)
            data_to_show = amazon_qwtt_inward
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Products", len(data_to_show))
            st.metric("Total Flipkart Sales", f"{data_to_show['Final Sale Units'].sum():,.0f}")
        with col2:
            st.metric("Total Amazon Sales", f"{data_to_show['Amazon Sales'].sum():,.0f}")
            st.metric("Total Amazon Stock", f"{data_to_show['Amazon Stock'].sum():,.0f}")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            data_to_show.to_excel(writer, index=False)
        st.download_button(
            label="📥 Download Excel",
            data=buffer.getvalue(),
            file_name="amazon_qwtt_inward.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("👈 Please upload all required files from the sidebar to begin analysis.")
    st.markdown("""
    ### Required Files:
    1. QWTT Inventory (Excel/CSV)
    2. Amazon Stock (CSV)
    3. Flipkart Business Report (Excel)
    4. Amazon Business Report (Excel)
    5. Amazon PM (Excel)
    6. Flipkart PM (Excel)
    7. Flipkart Easycom Inventory (CSV)
    """)
