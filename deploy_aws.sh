#!/bin/bash
# Despliegue en AWS (compatible con AWS Academy / Learner Lab):
# usa la VPC y subred POR DEFECTO, no crea roles IAM ni políticas ni VPCs.
set -euo pipefail
cd "$(dirname "$0")"

REGION=$(aws configure get region || true)
REGION=${REGION:-us-east-1}
export AWS_DEFAULT_REGION="$REGION"
echo "Región: $REGION"

# ── 1. VPC por defecto y una subred pública ────────────────────────────────
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
  --query 'Vpcs[0].VpcId' --output text)
echo "VPC por defecto: $VPC_ID"

# Las subredes default-for-az de la VPC por defecto son públicas
# (tienen ruta al Internet Gateway y asignan IP pública automáticamente).
SUBNET_ID=$(aws ec2 describe-subnets \
  --filters Name=vpc-id,Values="$VPC_ID" Name=default-for-az,Values=true \
  --query 'Subnets[0].SubnetId' --output text)
echo "Subred pública: $SUBNET_ID"

# ── 2. Security group mundial-sg (80, 8000, 22) ────────────────────────────
SG_ID=$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=mundial-sg Name=vpc-id,Values="$VPC_ID" \
  --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
  SG_ID=$(aws ec2 create-security-group \
    --group-name mundial-sg \
    --description "Mundial app: HTTP 80, app 8000, SSH 22" \
    --vpc-id "$VPC_ID" \
    --query 'GroupId' --output text)
  for PUERTO in 80 8000 22; do
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
      --protocol tcp --port "$PUERTO" --cidr 0.0.0.0/0 > /dev/null
  done
  echo "Security group creado: $SG_ID (puertos 80, 8000 y 22 abiertos)"
else
  echo "Security group ya existía: $SG_ID"
fi

# ── 3. AMI de Ubuntu (parámetro público de Canonical; con fallback) ────────
AMI_ID=$(aws ssm get-parameter \
  --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
  --query 'Parameter.Value' --output text 2>/dev/null || true)
if [ -z "$AMI_ID" ] || [ "$AMI_ID" = "None" ]; then
  AMI_ID=$(aws ec2 describe-images --owners 099720109477 \
    --filters 'Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*' \
              'Name=state,Values=available' \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)
fi
echo "AMI Ubuntu 24.04: $AMI_ID"

# ── 4. Key pair de AWS Academy (vockey) si existe, para SSH opcional ───────
KEY_OPT=()
if aws ec2 describe-key-pairs --key-names vockey > /dev/null 2>&1; then
  KEY_OPT=(--key-name vockey)
  echo "Key pair: vockey"
fi

# ── 5. Lanzar la instancia con IP pública + user_data.sh ───────────────────
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --subnet-id "$SUBNET_ID" \
  --security-group-ids "$SG_ID" \
  --associate-public-ip-address \
  "${KEY_OPT[@]}" \
  --user-data file://user_data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mundial-web}]' \
  --query 'Instances[0].InstanceId' --output text)
echo "Instancia lanzada: $INSTANCE_ID"

# ── 6. Esperar y mostrar la IP pública ─────────────────────────────────────
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo ""
echo "===================================================="
echo "  Instancia : $INSTANCE_ID"
echo "  IP pública: $IP"
echo "  App       : http://$IP        (puerto 80)"
echo "  App       : http://$IP:8000   (puerto 8000)"
echo "===================================================="
echo "El user-data tarda ~2-4 min en instalar Docker y levantar la app."
