# s3-cost

Scripts to calculate and estimate AWS S3 bucket costs.

## Scripts

1.  **`s3_cost_check.py`**: Uses AWS Cost Explorer to provide accurate cost breakdowns (Storage, Requests, Data Transfer) for one or more buckets.
    *   **Requirement**: `aws:s3:bucket` Cost Allocation Tag must be enabled in the AWS Billing Console.
2.  **`s3_usage_estimate.py`**: Uses CloudWatch metrics to *estimate* storage costs.
    *   **Limitation**: Does not track Data Transfer or Requests.

## ⚠️ Important Configuration Required

To use `s3_cost_check.py` (the accurate script), you **MUST** enable the Cost Allocation Tag for S3 buckets. By default, AWS provides total S3 costs, but it does **not** break them down by bucket name unless you enable this tag.

### How to Enable the Tag:
1.  Log into the **AWS Billing and Cost Management Console**.
2.  In the navigation pane, choose **Cost allocation tags**.
3.  Select the **AWS-generated cost allocation tags** tab.
4.  Search for `aws:s3:bucket`.
5.  Select the checkbox next to it and click **Activate**.
6.  **Wait**: It can take up to 24 hours for the tag to apply and for data to start populating in Cost Explorer.

## Prerequisites

*   Python 3.9+
*   [uv](https://github.com/astral-sh/uv) (for dependency management)
*   AWS Credentials configured (e.g., `~/.aws/credentials` or environment variables).

## Setup & Usage with uv

This project uses `uv` to manage dependencies and virtual environments.

### 1. Install uv
If you haven't installed `uv` yet:
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Run Scripts (Easiest Method)
You can run the scripts directly using `uv run`. This command automatically creates the virtual environment, installs dependencies from `pyproject.toml`, and executes the script.

```bash
# Run Cost Explorer script
uv run s3_cost_check.py --buckets <bucket-name>

# Run CloudWatch estimation script
uv run s3_usage_estimate.py --bucket <bucket-name>
```

### 3. Manual Virtual Environment Activation (Optional)
If you prefer to activate the virtual environment manually (e.g., for your IDE):

1.  **Create/Sync the environment**:
    ```bash
    uv sync
    ```
    This creates a `.venv` directory.

2.  **Activate the environment**:
    ```bash
    # macOS / Linux
    source .venv/bin/activate
    ```

3.  **Run scripts directly**:
    ```bash
    python s3_cost_check.py --buckets <bucket-name>
    ```