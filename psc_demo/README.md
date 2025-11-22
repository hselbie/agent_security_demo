# Agent Engine: Secure Database Access Demo (PSC + VPC-SC)

This demo showcases how to build and deploy a secure AI agent using the Agent Development Kit (ADK) on Agent Engine. The agent is designed to connect to a private Cloud SQL database, demonstrating a production-ready, enterprise-grade security posture.

## Architecture Overview

The core of this demo is to prove two key security principles:

1.  **Private Connectivity**: The agent, running in Google's managed environment, communicates with your Cloud SQL database exclusively over a private network connection using **Private Service Connect (PSC)**. No traffic travels over the public internet.
2.  **Data Exfiltration Prevention**: The entire system is secured within a **VPC Service Controls (VPC-SC)** perimeter. This virtual firewall ensures that your data cannot leave the secure environment and that only authorized services (like our specific Agent Engine) can interact with your database.

![Architecture Diagram](https://i.imgur.com/your-diagram-image-url.png)  <!-- You can create and upload a diagram to replace this link -->

## Prerequisites

Before you begin, ensure you have the following:

1.  **gcloud CLI**: Make sure the Google Cloud CLI is installed and authenticated (`gcloud auth login`).
2.  **Permissions**: You need an IAM role with permissions to create and manage VPCs, Cloud SQL, Agent Engine, and VPC Service Controls. Roles like `Owner` or `Editor` on a project are sufficient for a demo.
3.  **Organization ID**: VPC Service Controls requires an Organization. Find your ID with `gcloud organizations list`.
4.  **Python Environment**: A Python 3.9+ environment with `pip` installed.

## How to Run the Demo

The demo is broken down into a series of numbered shell scripts and Python files. Run them in order.

**Important:** Before running the scripts, you must edit the `variables.sh` file to set your specific `PROJECT_ID`, `ORGANIZATION_ID`, and other required values.

---

### Step 1: Set Up the Private Database

This script creates a new VPC, a subnet, and a private-only Cloud SQL for PostgreSQL instance. It then creates a simple `employees` table and populates it with sample data.

```bash
./01_setup_database.sh
```

---

### Step 2: Create the Private Service Connect (PSC) Endpoint

This script creates the secure network endpoint in your VPC that allows Agent Engine to privately connect to your network resources.

```bash
./02_setup_psc.sh
```

---

### Step 3: Configure the VPC Service Controls Perimeter

This script builds the security "wall" around your project and its services. It creates the perimeter and adds an ingress rule that explicitly allows the Agent Engine service to communicate with the services inside.

```bash
./03_setup_vpc_sc.sh
```

---

### Step 4: Deploy the ADK Agent

This Python script deploys the agent defined in `agent.py` to Agent Engine. It configures the agent to use the secure VPC network we created.

First, install the required Python packages:
```bash
pip install -r requirements.txt
```

Then, run the deployment script:
```bash
python3 04_deploy_agent.py
```
This step will take a few minutes as it builds and deploys the agent's container.

---

### Step 5: Test the Agent's Secure Connection

This script invokes the deployed agent and asks it to query the database. A successful run proves that the entire secure connection (Agent Engine -> PSC -> Cloud SQL) is working correctly.

```bash
python3 05_test_agent.py
```
You should see the agent return the employee data: `[('Alice', 'Engineer'), ('Bob', 'Manager')]`.

---

### Step 6: Verify the Security Perimeter

This is the final and most crucial step. We will attempt to connect to our private Cloud SQL database from outside the VPC-SC perimeter.

```bash
./06_verify_security.sh
```

This command **is expected to fail**. The error message will explicitly state that the request was blocked by a VPC Service Controls policy. This proves that our security perimeter is active and successfully preventing unauthorized access and potential data exfiltration.
