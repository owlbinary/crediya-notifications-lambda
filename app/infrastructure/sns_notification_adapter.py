import os
import boto3
from app.infrastructure.logger import get_logger
from app.application.ports import EmailNotificationPort
from dotenv import load_dotenv
load_dotenv()

logger = get_logger()

class SNSNotificationAdapter(EmailNotificationPort):
    def __init__(self, sns_topic_arn: str, aws_region: str = None):
        self.sns_topic_arn = sns_topic_arn
        self.aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        self.sns = boto3.client("sns", region_name=self.aws_region)

    def send_email_notification(self, message_body: str):
        logger.info(f"Enviando notificación SNS: {self.sns_topic_arn}")
        response = self.sns.publish(
            TopicArn=self.sns_topic_arn,
            Message=message_body
        )
        logger.info(f"Notificación enviada. MessageId: {response.get('MessageId')}")
