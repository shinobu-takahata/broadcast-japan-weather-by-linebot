import * as path from "node:path";
import * as cdk from "aws-cdk-lib";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import type { Construct } from "constructs";

export class WeatherBroadcastStack extends cdk.Stack {
	constructor(scope: Construct, id: string, props?: cdk.StackProps) {
		super(scope, id, props);

		// =============================================
		// DynamoDB Users Table
		// =============================================
		const usersTable = new dynamodb.Table(this, "UsersTable", {
			tableName: "WeatherBroadcast-Users",
			partitionKey: {
				name: "userId",
				type: dynamodb.AttributeType.STRING,
			},
			billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
			pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
			removalPolicy: cdk.RemovalPolicy.DESTROY,
		});

		// =============================================
		// Secrets Manager
		// =============================================
		const lineChannelSecret = new secretsmanager.Secret(
			this,
			"LineChannelSecret",
			{
				secretName: "line-channel-secret",
				description: "LINE Channel Secret for webhook verification",
			},
		);

		const lineChannelAccessToken = new secretsmanager.Secret(
			this,
			"LineChannelAccessToken",
			{
				secretName: "line-channel-access-token",
				description: "LINE Channel Access Token for messaging API",
			},
		);

		const weatherApiKey = new secretsmanager.Secret(
			this,
			"WeatherApiKey",
			{
				secretName: "weatherapi-api-key",
				description: "WeatherAPI API Key for weather data",
			},
		);

		// =============================================
		// Lambda - Webhook Handler
		// =============================================
		const webhookLogGroup = new logs.LogGroup(this, "WebhookHandlerLogGroup", {
			logGroupName: "/aws/lambda/weather-broadcast-line-webhook-handler",
			retention: logs.RetentionDays.ONE_MONTH,
			removalPolicy: cdk.RemovalPolicy.DESTROY,
		});

		const appCode = lambda.Code.fromAsset(
			path.join(__dirname, "../../app"),
			{
				bundling: {
					image: lambda.Runtime.PYTHON_3_12.bundlingImage,
					command: [
						"bash",
						"-c",
						"pip install -r requirements.txt -t /asset-output && rsync -au --exclude '.venv' --exclude '__pycache__' --exclude 'tests' --exclude '.devcontainer' --exclude '*.pyc' --exclude 'pyproject.toml' --exclude 'uv.lock' --exclude 'Dockerfile' --exclude 'requirements.txt' . /asset-output",
					],
				},
				exclude: [
					".venv",
					"__pycache__",
					"tests",
					".devcontainer",
					"*.pyc",
					"pyproject.toml",
					"uv.lock",
					"Dockerfile",
				],
			},
		);

		const webhookHandler = new lambda.Function(this, "LineWebhookHandler", {
			functionName: "weather-broadcast-line-webhook-handler",
			runtime: lambda.Runtime.PYTHON_3_12,
			handler: "handlers.webhook.handler",
			code: appCode,
			timeout: cdk.Duration.seconds(30),
			memorySize: 256,
			architecture: lambda.Architecture.X86_64,
			environment: {
				TABLE_NAME: usersTable.tableName,
				LINE_CHANNEL_SECRET_NAME: lineChannelSecret.secretName,
				LINE_CHANNEL_ACCESS_TOKEN_NAME: lineChannelAccessToken.secretName,
			},
			logGroup: webhookLogGroup,
		});

		// Webhook Lambda permissions
		usersTable.grantReadWriteData(webhookHandler);
		lineChannelSecret.grantRead(webhookHandler);
		lineChannelAccessToken.grantRead(webhookHandler);
		// =============================================
		// Lambda - Broadcast Handler
		// =============================================
		const broadcastLogGroup = new logs.LogGroup(
			this,
			"BroadcastHandlerLogGroup",
			{
				logGroupName: "/aws/lambda/weather-broadcast-weather-broadcast-handler",
				retention: logs.RetentionDays.ONE_MONTH,
				removalPolicy: cdk.RemovalPolicy.DESTROY,
			},
		);

		const broadcastHandler = new lambda.Function(
			this,
			"WeatherBroadcastHandler",
			{
				functionName: "weather-broadcast-weather-broadcast-handler",
				runtime: lambda.Runtime.PYTHON_3_12,
				handler: "handlers.broadcast.handler",
				code: appCode,
				timeout: cdk.Duration.seconds(300),
				memorySize: 512,
				architecture: lambda.Architecture.X86_64,
				environment: {
					TABLE_NAME: usersTable.tableName,
					LINE_CHANNEL_ACCESS_TOKEN_NAME: lineChannelAccessToken.secretName,
					WEATHERAPI_API_KEY_NAME: weatherApiKey.secretName,
				},
				logGroup: broadcastLogGroup,
			},
		);

		// Broadcast Lambda permissions
		usersTable.grantReadData(broadcastHandler);
		lineChannelAccessToken.grantRead(broadcastHandler);
		weatherApiKey.grantRead(broadcastHandler);

		// =============================================
		// API Gateway
		// =============================================
		const api = new apigateway.RestApi(this, "WebhookApi", {
			restApiName: "weather-broadcast-webhook-api",
			endpointTypes: [apigateway.EndpointType.REGIONAL],
			deployOptions: {
				stageName: "prod",
			},
		});

		const webhookResource = api.root.addResource("webhook");
		webhookResource.addMethod(
			"POST",
			new apigateway.LambdaIntegration(webhookHandler, {
				proxy: true,
			}),
		);

		// =============================================
		// EventBridge Schedule Rule
		// =============================================
		new events.Rule(this, "WeatherBroadcastSchedule", {
			ruleName: "weather-broadcast-schedule",
			description: "Trigger weather broadcast at 9:00 JST daily",
			schedule: events.Schedule.expression("cron(0 0 * * ? *)"),
			enabled: true,
			targets: [new targets.LambdaFunction(broadcastHandler)],
		});

		// =============================================
		// Stack Outputs
		// =============================================
		new cdk.CfnOutput(this, "WebhookApiUrl", {
			value: `${api.url}webhook`,
			description: "LINE Webhook URL",
		});

		new cdk.CfnOutput(this, "UsersTableName", {
			value: usersTable.tableName,
			description: "Users table name",
		});
	}
}
