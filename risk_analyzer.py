#!/usr/bin/env python3
"""
Risk & Quality Issue Tracker - Analytics Module

This module analyzes incident data to identify risk patterns, calculate key metrics,
and generate actionable insights for risk management and compliance teams.

Author: Risk Analytics Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


class RiskAnalyzer:
    """
    Analyzes incident data to identify high-risk categories, recurring issues,
    and resolution patterns.
    """
    
    def __init__(self, data_path):
        """
        Initialize the RiskAnalyzer with incident data.
        
        Args:
            data_path (str): Path to the CSV file containing incident data
        """
        self.data_path = data_path
        self.df = None
        self.risk_summary = {}
        
    def load_data(self):
        """Load incident data from CSV file."""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"✓ Successfully loaded {len(self.df)} incident records\n")
        except FileNotFoundError:
            print(f"✗ Error: File not found at {self.data_path}")
            raise
        except Exception as e:
            print(f"✗ Error loading data: {str(e)}")
            raise
    
    def identify_high_risk_categories(self, threshold_percentile=75):
        """
        Identify categories with high risk based on severity and frequency.
        
        Args:
            threshold_percentile (int): Percentile threshold for risk classification
            
        Returns:
            pd.DataFrame: High-risk categories with metrics
        """
        # Define severity weights for risk scoring
        severity_weights = {
            'Critical': 4,
            'High': 3,
            'Medium': 2,
            'Low': 1
        }
        
        # Calculate risk metrics by category
        category_analysis = self.df.groupby('category').agg({
            'incident_id': 'count',  # Frequency
            'severity': lambda x: x.map(severity_weights).mean(),  # Avg severity score
            'resolution_time_hours': 'mean',  # Avg resolution time
            'recurrence': lambda x: (x == 'Yes').sum()  # Recurrence count
        }).round(2)
        
        category_analysis.columns = ['Incident_Count', 'Avg_Severity_Score', 
                                     'Avg_Resolution_Hours', 'Recurring_Incidents']
        
        # Calculate composite risk score
        # Risk = (Frequency * Severity * Recurrence Factor) + Resolution Time Factor
        category_analysis['Recurrence_Rate'] = (
            category_analysis['Recurring_Incidents'] / 
            category_analysis['Incident_Count'] * 100
        ).round(1)
        
        category_analysis['Risk_Score'] = (
            category_analysis['Incident_Count'] * 
            category_analysis['Avg_Severity_Score'] * 
            (1 + category_analysis['Recurrence_Rate'] / 100) +
            category_analysis['Avg_Resolution_Hours'] / 10
        ).round(2)
        
        # Identify high-risk categories (top 75th percentile by default)
        risk_threshold = category_analysis['Risk_Score'].quantile(
            threshold_percentile / 100
        )
        
        high_risk = category_analysis[
            category_analysis['Risk_Score'] >= risk_threshold
        ].sort_values('Risk_Score', ascending=False)
        
        self.risk_summary['high_risk_categories'] = high_risk
        return high_risk
    
    def calculate_resolution_metrics(self):
        """
        Calculate average resolution time by category and severity.
        
        Returns:
            tuple: (by_category, by_severity) DataFrames with resolution metrics
        """
        # Resolution time by category
        by_category = self.df.groupby('category').agg({
            'resolution_time_hours': ['mean', 'median', 'min', 'max', 'std']
        }).round(2)
        
        by_category.columns = ['Avg_Hours', 'Median_Hours', 'Min_Hours', 
                              'Max_Hours', 'Std_Dev']
        by_category = by_category.sort_values('Avg_Hours', ascending=False)
        
        # Resolution time by severity
        by_severity = self.df.groupby('severity').agg({
            'resolution_time_hours': ['mean', 'median', 'count']
        }).round(2)
        
        by_severity.columns = ['Avg_Hours', 'Median_Hours', 'Incident_Count']
        
        # Define proper severity order
        severity_order = ['Critical', 'High', 'Medium', 'Low']
        by_severity = by_severity.reindex(severity_order)
        
        self.risk_summary['resolution_by_category'] = by_category
        self.risk_summary['resolution_by_severity'] = by_severity
        
        return by_category, by_severity
    
    def detect_recurring_issues(self):
        """
        Identify and analyze recurring issues that require systematic intervention.
        
        Returns:
            pd.DataFrame: Analysis of recurring issues by category and root cause
        """
        # Filter recurring incidents
        recurring = self.df[self.df['recurrence'] == 'Yes'].copy()
        
        if recurring.empty:
            print("No recurring issues detected.")
            return pd.DataFrame()
        
        # Analyze by category
        category_recurrence = recurring.groupby('category').agg({
            'incident_id': 'count',
            'severity': lambda x: x.mode()[0] if not x.mode().empty else 'N/A',
            'resolution_time_hours': 'mean'
        }).round(2)
        
        category_recurrence.columns = ['Recurring_Count', 'Most_Common_Severity', 
                                       'Avg_Resolution_Hours']
        category_recurrence = category_recurrence.sort_values(
            'Recurring_Count', ascending=False
        )
        
        # Analyze top root causes for recurring issues
        root_cause_analysis = recurring.groupby('root_cause').agg({
            'incident_id': 'count',
            'category': lambda x: ', '.join(x.unique())
        }).sort_values('incident_id', ascending=False).head(10)
        
        root_cause_analysis.columns = ['Occurrence_Count', 'Affected_Categories']
        
        self.risk_summary['recurring_by_category'] = category_recurrence
        self.risk_summary['top_recurring_root_causes'] = root_cause_analysis
        
        return category_recurrence, root_cause_analysis
    
    def generate_severity_distribution(self):
        """
        Generate severity distribution analysis across all incidents.
        
        Returns:
            pd.DataFrame: Severity distribution with percentages
        """
        severity_dist = self.df['severity'].value_counts().to_frame()
        severity_dist.columns = ['Count']
        severity_dist['Percentage'] = (
            severity_dist['Count'] / len(self.df) * 100
        ).round(1)
        
        # Reindex in proper severity order
        severity_order = ['Critical', 'High', 'Medium', 'Low']
        severity_dist = severity_dist.reindex(severity_order)
        
        self.risk_summary['severity_distribution'] = severity_dist
        return severity_dist
    
    def print_executive_summary(self):
        """
        Generate and print a comprehensive executive risk summary report.
        """
        print("=" * 80)
        print("EXECUTIVE RISK SUMMARY REPORT")
        print("=" * 80)
        print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Analysis Period: All Available Data")
        print(f"Total Incidents Analyzed: {len(self.df)}")
        print("=" * 80)
        
        # Section 1: Overall Risk Profile
        print("\n" + "▶ " + "OVERALL RISK PROFILE".ljust(78) + "◀")
        print("-" * 80)
        
        severity_dist = self.risk_summary.get('severity_distribution')
        if severity_dist is not None:
            print("\nSeverity Distribution:")
            for severity, row in severity_dist.iterrows():
                bar = "█" * int(row['Percentage'] / 2)
                print(f"  {severity:12s}: {int(row['Count']):3d} incidents "
                      f"({row['Percentage']:5.1f}%) {bar}")
        
        # Calculate recurrence rate
        recurrence_rate = (self.df['recurrence'] == 'Yes').sum() / len(self.df) * 100
        print(f"\nOverall Recurrence Rate: {recurrence_rate:.1f}%")
        
        # Section 2: High-Risk Categories
        print("\n" + "▶ " + "HIGH-RISK CATEGORIES (Immediate Attention Required)".ljust(78) + "◀")
        print("-" * 80)
        
        high_risk = self.risk_summary.get('high_risk_categories')
        if high_risk is not None and not high_risk.empty:
            print("\nRisk scores are calculated based on frequency, severity, recurrence, and resolution time.")
            print(f"\n{'Category':<20} {'Risk Score':<12} {'Incidents':<12} {'Recurrence %':<15} {'Avg Resolution'}")
            print("-" * 80)
            for category, row in high_risk.iterrows():
                print(f"{category:<20} {row['Risk_Score']:<12.2f} "
                      f"{int(row['Incident_Count']):<12} "
                      f"{row['Recurrence_Rate']:<15.1f} "
                      f"{row['Avg_Resolution_Hours']:.1f} hours")
            
            print("\n⚠ CRITICAL INSIGHT:")
            top_risk = high_risk.index[0]
            top_score = high_risk.iloc[0]['Risk_Score']
            print(f"  '{top_risk}' presents the highest risk (score: {top_score:.2f})")
            print(f"  This category requires immediate systematic intervention.")
        
        # Section 3: Resolution Performance
        print("\n" + "▶ " + "RESOLUTION TIME ANALYSIS".ljust(78) + "◀")
        print("-" * 80)
        
        by_category = self.risk_summary.get('resolution_by_category')
        if by_category is not None:
            print("\nAverage Resolution Time by Category:")
            print(f"\n{'Category':<20} {'Avg Hours':<12} {'Median Hours':<15} {'Range'}")
            print("-" * 80)
            for category, row in by_category.iterrows():
                range_str = f"{row['Min_Hours']:.0f} - {row['Max_Hours']:.0f}"
                print(f"{category:<20} {row['Avg_Hours']:<12.1f} "
                      f"{row['Median_Hours']:<15.1f} {range_str}")
        
        by_severity = self.risk_summary.get('resolution_by_severity')
        if by_severity is not None:
            print("\nResolution Time by Severity Level:")
            for severity, row in by_severity.iterrows():
                print(f"  {severity:10s}: {row['Avg_Hours']:6.1f} hours average "
                      f"({int(row['Incident_Count'])} incidents)")
        
        # Section 4: Recurring Issues
        print("\n" + "▶ " + "RECURRING ISSUES (Systemic Problems)".ljust(78) + "◀")
        print("-" * 80)
        
        recurring_cat = self.risk_summary.get('recurring_by_category')
        if recurring_cat is not None and not recurring_cat.empty:
            print("\nRecurring Issues by Category:")
            print(f"\n{'Category':<20} {'Recurring Count':<18} {'Most Common Severity':<25} {'Avg Resolution'}")
            print("-" * 80)
            for category, row in recurring_cat.iterrows():
                print(f"{category:<20} {int(row['Recurring_Count']):<18} "
                      f"{row['Most_Common_Severity']:<25} "
                      f"{row['Avg_Resolution_Hours']:.1f} hours")
            
            root_causes = self.risk_summary.get('top_recurring_root_causes')
            if root_causes is not None and not root_causes.empty:
                print("\nTop Recurring Root Causes:")
                for i, (cause, row) in enumerate(root_causes.head(5).iterrows(), 1):
                    print(f"  {i}. {cause} ({int(row['Occurrence_Count'])} occurrences)")
                    print(f"     Affects: {row['Affected_Categories']}")
        
        # Section 5: Recommendations
        print("\n" + "▶ " + "KEY RECOMMENDATIONS".ljust(78) + "◀")
        print("-" * 80)
        
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['title']}")
            print(f"   {rec['description']}")
        
        print("\n" + "=" * 80)
        print("END OF EXECUTIVE SUMMARY")
        print("=" * 80 + "\n")
    
    def _generate_recommendations(self):
        """
        Generate actionable recommendations based on analysis.
        
        Returns:
            list: List of recommendation dictionaries
        """
        recommendations = []
        
        # Recommendation 1: High-risk categories
        high_risk = self.risk_summary.get('high_risk_categories')
        if high_risk is not None and not high_risk.empty:
            top_category = high_risk.index[0]
            recommendations.append({
                'title': f"Implement Risk Mitigation Plan for '{top_category}'",
                'description': f"Develop comprehensive controls and process improvements "
                             f"to address the highest-risk category. Consider root cause "
                             f"analysis workshops and enhanced monitoring."
            })
        
        # Recommendation 2: Recurring issues
        recurring_cat = self.risk_summary.get('recurring_by_category')
        if recurring_cat is not None and not recurring_cat.empty:
            recommendations.append({
                'title': "Address Systemic Issues Through Process Redesign",
                'description': f"Focus on eliminating recurring issues which represent "
                             f"{len(recurring_cat)} categories. Implement preventive "
                             f"controls rather than reactive fixes."
            })
        
        # Recommendation 3: Critical incidents
        critical_count = len(self.df[self.df['severity'] == 'Critical'])
        if critical_count > 0:
            avg_critical_time = self.df[self.df['severity'] == 'Critical']['resolution_time_hours'].mean()
            recommendations.append({
                'title': "Strengthen Critical Incident Response Capabilities",
                'description': f"With {critical_count} critical incidents averaging "
                             f"{avg_critical_time:.1f} hours to resolve, enhance emergency "
                             f"response procedures and resource allocation."
            })
        
        # Recommendation 4: Resolution time
        by_category = self.risk_summary.get('resolution_by_category')
        if by_category is not None and not by_category.empty:
            slowest = by_category.index[0]
            recommendations.append({
                'title': f"Optimize Resolution Processes for '{slowest}'",
                'description': f"Investigate delays in this category and implement process "
                             f"improvements, additional training, or automation to reduce "
                             f"resolution time."
            })
        
        # Recommendation 5: Compliance and monitoring
        recommendations.append({
            'title': "Enhance Continuous Monitoring and Compliance Framework",
            'description': "Implement real-time alerting for high-risk patterns and "
                         "establish regular executive reviews to ensure prompt action "
                         "on emerging risks."
        })
        
        return recommendations
    
    def run_complete_analysis(self):
        """
        Execute complete risk analysis workflow.
        """
        print("\n🔍 Starting Risk & Quality Issue Analysis...\n")
        
        # Load data
        self.load_data()
        
        # Run all analyses
        print("📊 Analyzing risk categories...")
        self.identify_high_risk_categories()
        
        print("⏱  Calculating resolution metrics...")
        self.calculate_resolution_metrics()
        
        print("🔄 Detecting recurring issues...")
        self.detect_recurring_issues()
        
        print("📈 Generating severity distribution...")
        self.generate_severity_distribution()
        
        print("\n✓ Analysis complete!\n")
        
        # Print executive summary
        self.print_executive_summary()
    
    def export_results(self, output_dir='output'):
        """
        Export analysis results to CSV files.
        
        Args:
            output_dir (str): Directory to save output files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Export each analysis component
        if 'high_risk_categories' in self.risk_summary:
            self.risk_summary['high_risk_categories'].to_csv(
                output_path / 'high_risk_categories.csv'
            )
        
        if 'resolution_by_category' in self.risk_summary:
            self.risk_summary['resolution_by_category'].to_csv(
                output_path / 'resolution_by_category.csv'
            )
        
        if 'recurring_by_category' in self.risk_summary:
            self.risk_summary['recurring_by_category'].to_csv(
                output_path / 'recurring_by_category.csv'
            )
        
        print(f"✓ Results exported to '{output_dir}/' directory\n")
    
    def generate_risk_register(self, output_path='risk_register.csv'):
        """
        Generate a comprehensive risk register CSV suitable for risk management processes.
        
        The risk register includes risk identification, assessment, and mitigation details
        that can be used to support governance and compliance activities.
        
        Args:
            output_path (str): Path to save the risk register CSV
        """
        risk_register = []
        risk_id = 1
        
        # Get analysis results
        high_risk = self.risk_summary.get('high_risk_categories')
        recurring = self.risk_summary.get('recurring_by_category')
        resolution = self.risk_summary.get('resolution_by_category')
        
        if high_risk is None:
            print("⚠ Run complete analysis before generating risk register")
            return
        
        # Generate risk register entries for each high-risk category
        for category, row in high_risk.iterrows():
            risk_score = row['Risk_Score']
            incident_count = int(row['Incident_Count'])
            recurrence_rate = row['Recurrence_Rate']
            avg_resolution = row['Avg_Resolution_Hours']
            
            # Determine risk level based on risk score
            if risk_score >= 50:
                risk_level = 'Critical'
                likelihood = 'Very High'
            elif risk_score >= 30:
                risk_level = 'High'
                likelihood = 'High'
            elif risk_score >= 15:
                risk_level = 'Medium'
                likelihood = 'Medium'
            else:
                risk_level = 'Low'
                likelihood = 'Low'
            
            # Determine impact based on resolution time
            if avg_resolution >= 40:
                impact = 'Severe'
            elif avg_resolution >= 20:
                impact = 'Major'
            elif avg_resolution >= 10:
                impact = 'Moderate'
            else:
                impact = 'Minor'
            
            # Build risk description
            is_recurring = category in recurring.index if recurring is not None else False
            recurrence_text = f" with {recurrence_rate:.0f}% recurrence rate" if is_recurring else ""
            
            risk_desc = (f"Elevated incident rate in {category} category "
                        f"({incident_count} incidents{recurrence_text}). "
                        f"Average resolution time of {avg_resolution:.1f} hours indicates "
                        f"potential resource or process constraints.")
            
            # Generate mitigation recommendations
            mitigations = []
            if recurrence_rate > 50:
                mitigations.append("Conduct root cause analysis to address systemic issues")
            if avg_resolution > 30:
                mitigations.append("Review and optimize incident response procedures")
            if incident_count > 8:
                mitigations.append("Implement preventive controls to reduce incident frequency")
            
            mitigation_text = "; ".join(mitigations) if mitigations else "Monitor trends and maintain current controls"
            
            # Determine status
            status = "Active - Mitigation Required" if risk_level in ['Critical', 'High'] else "Active - Monitoring"
            
            risk_register.append({
                'Risk_ID': f'RISK-{risk_id:03d}',
                'Category': category,
                'Risk_Description': risk_desc,
                'Risk_Level': risk_level,
                'Likelihood': likelihood,
                'Impact': impact,
                'Risk_Score': f"{risk_score:.2f}",
                'Incident_Count': incident_count,
                'Avg_Resolution_Hours': f"{avg_resolution:.1f}",
                'Recurrence_Rate_%': f"{recurrence_rate:.1f}",
                'Mitigation_Strategy': mitigation_text,
                'Status': status,
                'Review_Date': datetime.now().strftime('%Y-%m-%d')
            })
            
            risk_id += 1
        
        # Create DataFrame and export
        register_df = pd.DataFrame(risk_register)
        register_df.to_csv(output_path, index=False)
        
        print(f"✓ Risk register generated: '{output_path}'")
        print(f"  Total risks identified: {len(risk_register)}")
        print(f"  Critical/High risks: {len(register_df[register_df['Risk_Level'].isin(['Critical', 'High'])])}")
        
        return register_df


def main():
    """
    Main execution function for the Risk & Quality Issue Tracker.
    """
    # Define data path
    data_file = 'incident_data.csv'
    
    # Initialize analyzer
    analyzer = RiskAnalyzer(data_file)
    
    # Run complete analysis
    analyzer.run_complete_analysis()
    
    # Generate risk register
    analyzer.generate_risk_register()
    
    # Export additional results (optional)
    # analyzer.export_results()


if __name__ == "__main__":
    main()
