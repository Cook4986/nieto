# Experimental Music Festival Network: Data Summary

This document provides a high-level summary and visual breakdown of the data extracted from the 18 target Instagram profiles and their recent posts.

## 📊 Audience Reach: Top 5 Profiles by Followers
The extracted data shows a massive variance in audience size among the target list, with major general-arts festivals naturally eclipsing specialized contemporary music entities.

```mermaid
pie title "Top 5 Festivals by Follower Count"
    "lucernefestival" : 66014
    "berlinerfestspiele" : 55547
    "theaterderzeit" : 15483
    "impulse__festival" : 12289
    "steirischerherbst" : 11743
```

## 🔄 Network Engagement: Top Accounts by 'Following'
A key metric for mapping networks is looking at how many accounts a profile follows. A high "following" count often indicates a highly engaged, community-centric account.

```mermaid
pie title "Top Accounts by Outbound Follows"
    "musiktheatertage.wien" : 2060
    "impulse__festival" : 1803
    "berlinerfestspiele" : 1526
    "nymusikk" : 1378
    "steirischerherbst" : 1302
```
*Note: `musiktheatertage.wien` only has a fraction of the followers of `berlinerfestspiele`, but follows significantly more accounts, indicating a dense network mapping strategy on their part.*

## 🕸️ Network Graph: Top Mentioned Entities
By scanning the captions of the most recent posts across the ecosystem, the scraper uncovered **272 distinct outbound connections**. Below is a breakdown of the most frequently mentioned external entities in the current news cycle.

```mermaid
pie title "Most Mentioned Accounts (from Recent Posts)"
    "fabian_schellhorn" : 5
    "sofijapalurovic" : 4
    "vikingurolafsson" : 3
    "guillaumemusset" : 3
    "schmalztiegel" : 2
    "Other (Single Mentions)" : 255
```

### Mention Graph Architecture
A simplified view of how the edge connections are structured based on the extracted data:

```mermaid
graph LR
    A["berlinerfestspiele"] -->|Mention| B["@fabian_schellhorn"]
    A -->|Mention| C["@caokefei0831"]
    D["ruemlingen"] -->|Mention| E["@artist_example"]
    F["lucernefestival"] -->|Mention| G["@vikingurolafsson"]
    
    style A fill:#2b5e73,stroke:#fff,color:#fff
    style D fill:#2b5e73,stroke:#fff,color:#fff
    style F fill:#2b5e73,stroke:#fff,color:#fff
    style B fill:#c76251,stroke:#fff,color:#fff
    style G fill:#c76251,stroke:#fff,color:#fff
```

## 📋 Comprehensive Target Export Preview
The flat `client_export.csv` file distills the profile and post metadata into a single, easily readable row per target.

| Instagram Handle | Bio Snapshot | Followers | Following | External Link | Post Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **lucernefestival** | Welcome to Lucerne Festival... | 66,014 | 1,168 | `lucernefestival.ch` | 2,423 |
| **berlinerfestspiele** | Contemporary arts festival... | 55,547 | 1,526 | `berlinerfestspiele.de` | 2,891 |
| **theaterderzeit** | Das Magazin für Theater... | 15,483 | 1,029 | `tdz.de` | 2,746 |
| **ruemlingen** | Festival Neue Musik... | 1,268 | 359 | `neue-musik-ruemlingen.ch` | 109 |
| **musiktexte.online** | Monatlich erscheinende... | 886 | 414 | `musiktexte.online` | 107 |

> [!NOTE]
> **Actionable Next Step:** Load the generated `data/network.graphml` file into a visualizer like **Gephi** to see the full, interactive spatial map of all 282 nodes and 272 edges.
