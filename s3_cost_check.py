import boto3
import argparse
from datetime import datetime, timedelta
from tabulate import tabulate
import sys

def get_s3_costs(bucket_names, days, profile=None):
    """
    Calculates aggregated S3 costs for specific buckets using AWS Cost Explorer.
    """
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    ce = session.client('ce')

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Format dates as strings
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    buckets_str = ", ".join(f"'{b}'" for b in bucket_names)
    print(f"Fetching aggregated costs for buckets: {buckets_str}")
    print(f"Period: {start_str} to {end_str}...")

    try:
        # We need to filter by Service=S3 and Tag:aws:s3:bucket IN [bucket_names]
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_str,
                'End': end_str
            },
            Granularity='MONTHLY',
            Filter={
                'And': [
                    {
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': ['Amazon Simple Storage Service']
                        }
                    },
                    {
                        'Tags': {
                            'Key': 'aws:s3:bucket',
                            'Values': bucket_names
                        }
                    }
                ]
            },
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
            ]
        )
    except Exception as e:
        print(f"Error fetching data from Cost Explorer: {e}")
        print("Tip: Ensure the 'aws:s3:bucket' Cost Allocation Tag is enabled in the Billing Console.")
        sys.exit(1)

    results = response.get('ResultsByTime', [])
    
    cost_data = {}
    total_cost = 0.0

    # Categories for aggregation
    categories = {
        'Storage': ['TimedStorage', 'Storage'],
        'Requests': ['Requests'],
        'Data Transfer': ['DataTransfer', 'Out-Bytes', 'In-Bytes'],
        'Replication': ['Replication', 'C3DataTransfer']
    }

    detailed_rows = []

    for period in results:
        for group in period.get('Groups', []):
            usage_type = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            
            if amount == 0:
                continue

            total_cost += amount
            
            # Categorize
            category = 'Other'
            for cat, keywords in categories.items():
                if any(k in usage_type for k in keywords):
                    category = cat
                    break
            
            if category not in cost_data:
                cost_data[category] = 0.0
            cost_data[category] += amount
            
            detailed_rows.append([usage_type, category, f"${amount:.4f}"])

    # Prepare summary table
    summary_rows = [[cat, f"${cost:.4f}"] for cat, cost in cost_data.items()]
    summary_rows.sort(key=lambda x: x[1], reverse=True)
    summary_rows.append(["TOTAL", f"${total_cost:.4f}"])

    print("\n--- Aggregated Cost Summary ---")
    print(tabulate(summary_rows, headers=['Category', 'Cost'], tablefmt='simple'))

    print("\n--- Detailed Breakdown ---")
    detailed_rows.sort(key=lambda x: float(x[2].strip('$')), reverse=True)
    print(tabulate(detailed_rows, headers=['Usage Type', 'Category', 'Cost'], tablefmt='simple'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate aggregated S3 costs for multiple buckets.")
    parser.add_argument("--buckets", required=True, nargs='+', help="List of S3 bucket names.")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back (default: 30).")
    parser.add_argument("--profile", help="AWS CLI profile to use.")

    args = parser.parse_args()
    
    get_s3_costs(args.buckets, args.days, args.profile)
