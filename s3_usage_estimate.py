import boto3
import argparse
from datetime import datetime, timedelta
from tabulate import tabulate
import sys

def get_s3_storage_estimate(bucket_name, region, profile=None):
    """
    Estimates S3 storage costs using CloudWatch metrics.
    """
    session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
    cw = session.client('cloudwatch')

    print(f"Fetching CloudWatch metrics for bucket '{bucket_name}' in region '{region}'...")

    # Define storage types to check
    storage_types = [
        'StandardStorage',
        'IntelligentTieringFAStorage',
        'StandardIAStorage',
        'OneZoneIAStorage',
        'GlacierStorage',
        'DeepArchiveStorage'
    ]

    # Approximate pricing (USD per GB per Month) - simplified
    # Real pricing varies by region and tier volume.
    pricing = {
        'StandardStorage': 0.023,
        'IntelligentTieringFAStorage': 0.023, # Frequent Access
        'StandardIAStorage': 0.0125,
        'OneZoneIAStorage': 0.01,
        'GlacierStorage': 0.004,
        'DeepArchiveStorage': 0.00099
    }

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=2) # Look back 2 days to ensure metric availability

    results = []
    total_gb = 0.0
    total_est_cost = 0.0

    for stype in storage_types:
        try:
            response = cw.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='BucketSizeBytes',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': stype}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                # Get the latest datapoint
                latest = sorted(datapoints, key=lambda x: x['Timestamp'])[-1]
                bytes_val = latest['Average']
                gb_val = bytes_val / (1024**3)
                
                cost = gb_val * pricing.get(stype, 0.023)
                
                results.append([stype, f"{gb_val:.4f} GB", f"${cost:.4f}"])
                
                total_gb += gb_val
                total_est_cost += cost

        except Exception as e:
            print(f"Warning: Could not fetch metric for {stype}: {e}")

    print("\n--- Storage Cost Estimate (Monthly) ---")
    if not results:
        print("No storage metrics found. Note that CloudWatch metrics for S3 are reported once daily.")
    else:
        results.append(["TOTAL", f"{total_gb:.4f} GB", f"${total_est_cost:.4f}"])
        print(tabulate(results, headers=['Storage Type', 'Size', 'Est. Cost'], tablefmt='simple'))
        
    print("\n" + "="*60)
    print("DISCLAIMER: This is an ESTIMATE based on CloudWatch 'BucketSizeBytes'.")
    print("1. It does NOT include Data Transfer costs.")
    print("2. It does NOT include Request costs (PUT, GET, etc.).")
    print("3. It assumes standard pricing rates and does not account for free tiers or volume discounts.")
    print("4. CloudWatch S3 metrics are updated daily, so data may be up to 24 hours old.")
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate S3 storage costs using CloudWatch.")
    parser.add_argument("--bucket", required=True, help="The name of the S3 bucket.")
    parser.add_argument("--region", default="us-east-1", help="AWS Region (default: us-east-1).")
    parser.add_argument("--profile", help="AWS CLI profile to use.")

    args = parser.parse_args()
    
    get_s3_storage_estimate(args.bucket, args.region, args.profile)
