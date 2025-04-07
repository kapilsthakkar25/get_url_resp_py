To **automate branch locking** in **Azure DevOps (ADO)**, you can use either the **REST API** or **Azure CLI**, often integrated into your pipeline (YAML) or scheduled scripts. Here’s a quick guide using REST API and PowerShell.

---

### 🔒 Lock a Branch Using REST API (PowerShell Example)

```powershell
$organization = "your-org"
$project = "your-project"
$repositoryId = "your-repo-id"  # or use repo name in URL
$branchName = "refs/heads/main"  # fully qualified ref
$pat = "your-personal-access-token"

$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$pat"))

$body = @{
    name  = $branchName
    isLocked = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://dev.azure.com/$organization/$project/_apis/git/repositories/$repositoryId/refs?api-version=7.1-preview.1" `
    -Method Patch `
    -Headers @{Authorization=("Basic {0}" -f $base64AuthInfo)} `
    -ContentType "application/json" `
    -Body $body
```

> 🔐 **Note:** Locking prevents **pushes** to the branch but doesn't block PR merges. For that, use branch policies.

---

### ✅ Optional: Add to Azure DevOps Pipeline

You can add the above PowerShell to a pipeline stage:

```yaml
- task: PowerShell@2
  inputs:
    targetType: 'inline'
    script: |
      # Insert the PowerShell script above here
```

---

### 🔄 Alternative: Use Azure DevOps CLI

```bash
az repos ref update \
  --name "refs/heads/main" \
  --repository "your-repo-name" \
  --project "your-project" \
  --is-locked true
```

Make sure you have installed the [Azure DevOps extension](https://learn.microsoft.com/en-us/azure/devops/cli/?view=azure-devops).

---

Let me know if you want this scheduled or triggered post-release, or as part of a branch protection flow.
