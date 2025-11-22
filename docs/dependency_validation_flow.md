# Dependency Validation Flow

The following Mermaid diagram describes the VS Code pre-launch dependency validation and CI/CD signing flow.

```mermaid
%%{init: {'theme':'neutral','flowchart':{'curve':'basis'}} }%%
flowchart TD
    A[VS Code Launch Request] --> B{Pre-Launch Validation}
    B --> B1[Validate C# Projects<br/>.csproj sweep: TargetFramework + NuGet]
    B --> B2[Validate Python Requirements<br/>Duplication/Drift check]
    B --> B3[Validate Node Lockfile<br/>package-lock / yarn.lock / pnpm-lock.yaml]
    B1 --> C{All validations pass?}
    B2 --> C
    B3 --> C
    C -- No --> D[Block Launch<br/>Fix drift or missing artifacts]
    C -- Yes --> E[Launch Configurations]
    E --> E1[Launch PrecisePointway (coreclr)]
    E --> E2[Launch Node UI (node)]
    E --> E3[Launch Python Agent (python)]
    E1 -. optional .-> EC[Compound Launch<br/>All stacks together]
    E2 -. optional .-> EC
    E3 -. optional .-> EC

    subgraph CI/CD Pipeline
        P1[Run Validations (C#, Python, Node)] --> P2[Generate DependencyManifest.md]
        P2 --> P3[Create SHA-256 Checksum<br/>DependencyManifest.sha256]
        P3 --> P4[GPG Sign Manifest<br/>DependencyManifest.md.sig]
        P4 --> P5[Publish Artifacts<br/>dependency-validation-reports]
        P5 --> P6{Auditor Verification}
        P6 --> V1[Import Public Key<br/>gpg --import publickey.asc]
        V1 --> V2[Verify Signature<br/>gpg --verify *.sig *.md]
        V2 --> V3[Verify Checksum<br/>sha256sum -c *.sha256]
        V3 --> V4[Cross-check Fingerprint<br/>gpg --fingerprint KEY_ID]
    end

    EC --> P1
```

Open `docs/dependency_validation_flow.md` in VS Code to view the diagram (Mermaid preview extension recommended).
