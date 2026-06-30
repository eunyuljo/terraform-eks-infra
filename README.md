# Terraform EKS Infrastructure - IaC 운영 프로세스 가이드

## 📁 프로젝트 구조

```
terraform-eks-infra/
├── modules/                          # 재사용 가능한 Terraform 모듈
│   ├── vpc/                          # VPC, Subnet, NAT, IGW
│   ├── eks/                          # EKS Cluster, Node Group, OIDC
│   └── security-group/               # 범용 Security Group
│
├── live/                             # 실제 배포 단위 (환경 × 라이프사이클)
│   ├── dev/
│   │   ├── network/                  # dev 네트워크 (독립 state)
│   │   └── eks-cluster/              # dev EKS (독립 state)
│   ├── stg/
│   │   ├── network/
│   │   └── eks-cluster/
│   └── prod/
│       ├── network/
│       └── eks-cluster/
│
├── scripts/pr_review_checker/        # PR 리뷰 체크리스트 자동화 도구
└── .github/workflows/                # CI/CD 워크플로우
```

## 🏗️ 설계 원칙

### 1. 라이프사이클 분리
- **network/**: VPC, Subnet, NAT Gateway → 거의 변경되지 않음
- **eks-cluster/**: EKS, Node Group, IRSA → 상대적으로 자주 변경
- 각각 독립된 `terraform apply` 단위, 별도의 state 파일

### 2. 환경 격리 (디렉토리 기반)
- `live/{env}/{lifecycle}/` 구조로 **구조적 격리**
- workspace 미사용 → 실수로 다른 환경에 apply 불가능
- 환경별 독립된 state path:
  - `s3://myproject-terraform-state/dev/network/terraform.tfstate`
  - `s3://myproject-terraform-state/prod/eks-cluster/terraform.tfstate`

### 3. 모듈 재사용
- `modules/` 에 공통 로직 → `live/` 에서 환경별 값으로 호출
- 모듈 변경 시 영향 범위를 PR 리뷰로 확인

## 🔄 운영 프로세스

```
변경 요청 (Jira/Ticket)
    ↓
Feature Branch 생성
    ↓
Terraform 코드 변경
    ↓
PR 생성
    ↓
┌─────────────────────────────┐
│ 자동 검증 (GitHub Actions)   │
│ • terraform fmt -check      │
│ • terraform validate        │
│ • terraform plan            │
│ • PR Review Checklist 생성   │
└─────────────────────────────┘
    ↓
위험도 기반 승인
    • HIGH  → 시니어 엔지니어 + 고객 승인
    • MEDIUM → 시니어 엔지니어 승인
    • LOW   → 팀원 1명 승인
    ↓
Merge → terraform apply
    ↓
결과 알림 (Slack/Teams)
```

## 🚦 위험도 분류 기준

| 위험도 | 조건 | 예시 |
|--------|------|------|
| **HIGH** | 보안 약화, 리소스 삭제, prod 영향 | SG 0.0.0.0/0, IAM Admin, 노드그룹 삭제 |
| **MEDIUM** | 설정 변경, 스케일링 | 인스턴스 타입 변경, 서브넷 추가 |
| **LOW** | 태그, 설명 변경, dev 환경 | tags 수정, description 업데이트 |

## 🚀 사용법

### 배포
```bash
# dev 네트워크 배포
cd live/dev/network/
terraform init
terraform plan
terraform apply

# dev EKS 배포 (network 배포 후)
cd live/dev/eks-cluster/
terraform init
terraform plan
terraform apply
```

### PR 리뷰 체크리스트 (로컬 테스트)
```bash
cd scripts/
pip install -r requirements.txt
export GITHUB_TOKEN="ghp_xxx"
export REPO="owner/terraform-eks-infra"
export PR_NUMBER="1"
python -m pr_review_checker.main --dry-run
```

## 🏷️ 태깅 전략

모든 리소스에 아래 태그 적용:
- `Environment`: dev / stg / prod
- `ManagedBy`: terraform
- `Project`: myproject
- `Owner`: platform-team

## 🔒 보안 정책

- EKS 노드는 private subnet에만 배치
- Bastion SG는 내부 대역만 허용
- prod ALB SG만 외부 HTTPS 허용 (WAF 연동 전제)
- IAM은 최소 권한 원칙 (IRSA 활용)
