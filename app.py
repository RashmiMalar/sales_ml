import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend

from flask import Flask, request, render_template
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os

app = Flask(__name__)

# Load the model dictionary containing 'model' and 'accuracy'
model_data = joblib.load('sales_prediction_model (2).pkl')
model = model_data['model']

# Set matplotlib style for better looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

@app.route('/')
def index():
    return render_template('index.html', status_message="Ready to predict! Fill in the product and outlet details.")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Fetch form data
        form_data = {
            'Item_Identifier': request.form['Item_Identifier'],
            'Item_Weight': float(request.form['Item_Weight']),
            'Item_Fat_Content': request.form['Item_Fat_Content'],
            'Item_Visibility': float(request.form['Item_Visibility']),
            'Item_Type': request.form['Item_Type'],
            'Item_MRP': float(request.form['Item_MRP']),
            'Outlet_Identifier': request.form['Outlet_Identifier'],
            'Outlet_Establishment_Year': int(request.form['Outlet_Establishment_Year']),
            'Outlet_Size': request.form['Outlet_Size'],
            'Outlet_Location_Type': request.form['Outlet_Location_Type'],
            'Outlet_Type': request.form['Outlet_Type']
        }

        # Convert to DataFrame
        input_df = pd.DataFrame([form_data])

        # Make prediction
        prediction = model.predict(input_df)[0]

        # Create enhanced visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Sales Prediction Analytics Dashboard', fontsize=16, fontweight='bold', y=0.98)

        # 1. Prediction vs MRP Analysis
        mrp_range = np.linspace(form_data['Item_MRP'] * 0.5, form_data['Item_MRP'] * 1.5, 50)
        predicted_sales = []
        
        for mrp in mrp_range:
            temp_data = form_data.copy()
            temp_data['Item_MRP'] = mrp
            temp_df = pd.DataFrame([temp_data])
            pred = model.predict(temp_df)[0]
            predicted_sales.append(pred)
        
        ax1.plot(mrp_range, predicted_sales, color='#667eea', linewidth=3, label='Sales Trend')
        ax1.scatter(form_data['Item_MRP'], prediction, color='#f093fb', s=200, zorder=5, 
                   label=f'Your Product: ₹{prediction:.0f}', edgecolor='white', linewidth=2)
        ax1.set_xlabel('Item MRP (₹)', fontweight='bold')
        ax1.set_ylabel('Predicted Sales (₹)', fontweight='bold')
        ax1.set_title('Sales vs MRP Analysis', fontweight='bold', pad=20)
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 2. Sales Distribution by Outlet Type
        outlet_types = ['Supermarket Type1', 'Supermarket Type2', 'Supermarket Type3', 'Grocery Store']
        outlet_predictions = []
        
        for outlet in outlet_types:
            temp_data = form_data.copy()
            temp_data['Outlet_Type'] = outlet
            temp_df = pd.DataFrame([temp_data])
            pred = model.predict(temp_df)[0]
            outlet_predictions.append(pred)
        
        colors = ['#667eea', '#764ba2', '#f093fb', '#48bb78']
        bars = ax2.bar(outlet_types, outlet_predictions, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
        
        # Highlight current outlet type
        current_outlet_idx = outlet_types.index(form_data['Outlet_Type'])
        bars[current_outlet_idx].set_color('#ff6b6b')
        bars[current_outlet_idx].set_edgecolor('#fff')
        bars[current_outlet_idx].set_linewidth(3)
        
        ax2.set_xlabel('Outlet Type', fontweight='bold')
        ax2.set_ylabel('Predicted Sales (₹)', fontweight='bold')
        ax2.set_title('Sales by Outlet Type', fontweight='bold', pad=20)
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'₹{height:.0f}', ha='center', va='bottom', fontweight='bold')

        # 3. Location Impact Analysis
        locations = ['Tier 1', 'Tier 2', 'Tier 3']
        location_predictions = []
        
        for location in locations:
            temp_data = form_data.copy()
            temp_data['Outlet_Location_Type'] = location
            temp_df = pd.DataFrame([temp_data])
            pred = model.predict(temp_df)[0]
            location_predictions.append(pred)
        
        wedges, texts, autotexts = ax3.pie(location_predictions, labels=locations, autopct='₹%.0f',
                                          colors=['#667eea', '#764ba2', '#f093fb'], startangle=90,
                                          explode=[0.05 if loc == form_data['Outlet_Location_Type'] else 0 for loc in locations])
        
        ax3.set_title('Sales Distribution by Location', fontweight='bold', pad=20)
        
        # Style the pie chart text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        # 4. Key Metrics Summary
        ax4.axis('off')
        
        # Calculate some insights
        avg_prediction = np.mean([prediction] + outlet_predictions + location_predictions)
        max_potential = max(outlet_predictions + location_predictions)
        improvement_potential = ((max_potential - prediction) / prediction) * 100 if prediction > 0 else 0
        
        metrics_text = f"""
        📊 PREDICTION SUMMARY
        
        🎯 Predicted Sales: ₹{prediction:,.0f}
        
        📈 Market Average: ₹{avg_prediction:,.0f}
        
        🚀 Max Potential: ₹{max_potential:,.0f}
        
        💡 Improvement Scope: {improvement_potential:.1f}%
        
        🏪 Your Outlet: {form_data['Outlet_Type']}
        📍 Location: {form_data['Outlet_Location_Type']}
        🏷️ Category: {form_data['Item_Type']}
        💰 MRP: ₹{form_data['Item_MRP']:.2f}
        """
        
        ax4.text(0.1, 0.9, metrics_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
                facecolor='lightblue', alpha=0.8))

        plt.tight_layout()
        
        # Save plot to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()

        return render_template('index.html', 
                             prediction=round(prediction, 2), 
                             image_url=image_base64, 
                             status_message="Prediction completed successfully! 🎉")

    except Exception as e:
        return render_template('index.html', 
                             status_message=f"Error during prediction: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)