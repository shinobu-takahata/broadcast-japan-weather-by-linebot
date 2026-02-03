"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WeatherBroadcastStack = void 0;
const path = require("node:path");
const cdk = require("aws-cdk-lib");
const apigateway = require("aws-cdk-lib/aws-apigateway");
const dynamodb = require("aws-cdk-lib/aws-dynamodb");
const events = require("aws-cdk-lib/aws-events");
const targets = require("aws-cdk-lib/aws-events-targets");
const lambda = require("aws-cdk-lib/aws-lambda");
const logs = require("aws-cdk-lib/aws-logs");
const secretsmanager = require("aws-cdk-lib/aws-secretsmanager");
class WeatherBroadcastStack extends cdk.Stack {
    constructor(scope, id, props) {
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
        const lineChannelSecret = new secretsmanager.Secret(this, "LineChannelSecret", {
            secretName: "line-channel-secret",
            description: "LINE Channel Secret for webhook verification",
        });
        const lineChannelAccessToken = new secretsmanager.Secret(this, "LineChannelAccessToken", {
            secretName: "line-channel-access-token",
            description: "LINE Channel Access Token for messaging API",
        });
        const weatherApiKey = new secretsmanager.Secret(this, "WeatherApiKey", {
            secretName: "weatherapi-api-key",
            description: "WeatherAPI API Key for weather data",
        });
        // =============================================
        // Lambda - Webhook Handler
        // =============================================
        const webhookLogGroup = new logs.LogGroup(this, "WebhookHandlerLogGroup", {
            logGroupName: "/aws/lambda/weather-broadcast-line-webhook-handler",
            retention: logs.RetentionDays.ONE_MONTH,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
        });
        const appCode = lambda.Code.fromAsset(path.join(__dirname, "../../app"), {
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
        });
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
        const broadcastLogGroup = new logs.LogGroup(this, "BroadcastHandlerLogGroup", {
            logGroupName: "/aws/lambda/weather-broadcast-weather-broadcast-handler",
            retention: logs.RetentionDays.ONE_MONTH,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
        });
        const broadcastHandler = new lambda.Function(this, "WeatherBroadcastHandler", {
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
        });
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
        webhookResource.addMethod("POST", new apigateway.LambdaIntegration(webhookHandler, {
            proxy: true,
        }));
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
exports.WeatherBroadcastStack = WeatherBroadcastStack;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoid2VhdGhlci1icm9hZGNhc3Qtc3RhY2suanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi9saWIvd2VhdGhlci1icm9hZGNhc3Qtc3RhY2sudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQUEsa0NBQWtDO0FBQ2xDLG1DQUFtQztBQUNuQyx5REFBeUQ7QUFDekQscURBQXFEO0FBQ3JELGlEQUFpRDtBQUNqRCwwREFBMEQ7QUFDMUQsaURBQWlEO0FBQ2pELDZDQUE2QztBQUM3QyxpRUFBaUU7QUFHakUsTUFBYSxxQkFBc0IsU0FBUSxHQUFHLENBQUMsS0FBSztJQUNuRCxZQUFZLEtBQWdCLEVBQUUsRUFBVSxFQUFFLEtBQXNCO1FBQy9ELEtBQUssQ0FBQyxLQUFLLEVBQUUsRUFBRSxFQUFFLEtBQUssQ0FBQyxDQUFDO1FBRXhCLGdEQUFnRDtRQUNoRCx1QkFBdUI7UUFDdkIsZ0RBQWdEO1FBQ2hELE1BQU0sVUFBVSxHQUFHLElBQUksUUFBUSxDQUFDLEtBQUssQ0FBQyxJQUFJLEVBQUUsWUFBWSxFQUFFO1lBQ3pELFNBQVMsRUFBRSx3QkFBd0I7WUFDbkMsWUFBWSxFQUFFO2dCQUNiLElBQUksRUFBRSxRQUFRO2dCQUNkLElBQUksRUFBRSxRQUFRLENBQUMsYUFBYSxDQUFDLE1BQU07YUFDbkM7WUFDRCxXQUFXLEVBQUUsUUFBUSxDQUFDLFdBQVcsQ0FBQyxlQUFlO1lBQ2pELGdDQUFnQyxFQUFFLEVBQUUsMEJBQTBCLEVBQUUsSUFBSSxFQUFFO1lBQ3RFLGFBQWEsRUFBRSxHQUFHLENBQUMsYUFBYSxDQUFDLE9BQU87U0FDeEMsQ0FBQyxDQUFDO1FBRUgsZ0RBQWdEO1FBQ2hELGtCQUFrQjtRQUNsQixnREFBZ0Q7UUFDaEQsTUFBTSxpQkFBaUIsR0FBRyxJQUFJLGNBQWMsQ0FBQyxNQUFNLENBQ2xELElBQUksRUFDSixtQkFBbUIsRUFDbkI7WUFDQyxVQUFVLEVBQUUscUJBQXFCO1lBQ2pDLFdBQVcsRUFBRSw4Q0FBOEM7U0FDM0Qs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aEQsNEJBQTRCO1FBQzVCLGdEQUFnRDtRQUNoRCxJQUFJLE1BQU0sQ0FBQyxJQUFJLENBQUMsSUFBSSxFQUFFLDBCQUEwQixFQUFFO1lBQ2pELFFBQVEsRUFBRSw0QkFBNEI7WUFDdEMsV0FBVyxFQUFFLDZDQUE2QztZQUMxRCxRQUFRLEVBQUUsTUFBTSxDQUFDLFFBQVEsQ0FBQyxVQUFVLENBQUMsbUJBQW1CLENBQUM7WUFDekQsT0FBTyxFQUFFLElBQUk7WUFDYixPQUFPLEVBQUUsQ0FBQyxJQUFJLE9BQU8sQ0FBQyxjQUFjLENBQUMsZ0JBQWdCLENBQUMsQ0FBQztTQUN2RCxDQUFDLENBQUM7UUFFSCxnREFBZ0Q7UUFDaEQsZ0JBQWdCO1FBQ2hCLGdEQUFnRDtRQUNoRCxJQUFJLEdBQUcsQ0FBQyxTQUFTLENBQUMsSUFBSSxFQUFFLGVBQWUsRUFBRTtZQUN4QyxLQUFLLEVBQUUsR0FBRyxHQUFHLENBQUMsR0FBRyxTQUFTO1lBQzFCLFdBQVcsRUFBRSxrQkFBa0I7U0FDL0IsQ0FBQyxDQUFDO1FBRUgsSUFBSSxHQUFHLENBQUMsU0FBUyxDQUFDLElBQUksRUFBRSxnQkFBZ0IsRUFBRTtZQUN6QyxLQUFLLEVBQUUsVUFBVSxDQUFDLFNBQVM7WUFDM0IsV0FBVyxFQUFFLGtCQUFrQjtTQUMvQixDQUFDLENBQUM7SUFDSixDQUFDO0NBQ0Q7QUF0TEQsc0RBc0xDIiwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0ICogYXMgcGF0aCBmcm9tIFwibm9kZTpwYXRoXCI7XG5pbXBvcnQgKiBhcyBjZGsgZnJvbSBcImF3cy1jZGstbGliXCI7XG5pbXBvcnQgKiBhcyBhcGlnYXRld2F5IGZyb20gXCJhd3MtY2RrLWxpYi9hd3MtYXBpZ2F0ZXdheVwiO1xuaW1wb3J0ICogYXMgZHluYW1vZGIgZnJvbSBcImF3cy1jZGstbGliL2F3cy1keW5hbW9kYlwiO1xuaW1wb3J0ICogYXMgZXZlbnRzIGZyb20gXCJhd3MtY2RrLWxpYi9hd3MtZXZlbnRzXCI7XG5pbXBvcnQgKiBhcyB0YXJnZXRzIGZyb20gXCJhd3MtY2RrLWxpYi9hd3MtZXZlbnRzLXRhcmdldHNcIjtcbmltcG9ydCAqIGFzIGxhbWJkYSBmcm9tIFwiYXdzLWNkay1saWIvYXdzLWxhbWJkYVwiO1xuaW1wb3J0ICogYXMgbG9ncyBmcm9tIFwiYXdzLWNkay1saWIvYXdzLWxvZ3NcIjtcbmltcG9ydCAqIGFzIHNlY3JldHNtYW5hZ2VyIGZyb20gXCJhd3MtY2RrLWxpYi9hd3Mtc2VjcmV0c21hbmFnZXJcIjtcbmltcG9ydCB0eXBlIHsgQ29uc3RydWN0IH0gZnJvbSBcImNvbnN0cnVjdHNcIjtcblxuZXhwb3J0IGNsYXNzIFdlYXRoZXJCcm9hZGNhc3RTdGFjayBleHRlbmRzIGNkay5TdGFjayB7XG5cdGNvbnN0cnVjdG9yKHNjb3BlOiBDb25zdHJ1Y3QsIGlkOiBzdHJpbmcsIHByb3BzPzogY2RrLlN0YWNrUHJvcHMpIHtcblx0XHRzdXBlcihzY29wZSwgaWQsIHByb3BzKTtcblxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdC8vIER5bmFtb0RCIFVzZXJzIFRhYmxlXG5cdFx0Ly8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG5cdFx0Y29uc3QgdXNlcnNUYWJsZSA9IG5ldyBkeW5hbW9kYi5UYWJsZSh0aGlzLCBcIlVzZXJzVGFibGVcIiwge1xuXHRcdFx0dGFibGVOYW1lOiBcIldlYXRoZXJCcm9hZGNhc3QtVXNlcnNcIixcblx0XHRcdHBhcnRpdGlvbktleToge1xuXHRcdFx0XHRuYW1lOiBcInVzZXJJZFwiLFxuXHRcdFx0XHR0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyxcblx0XHRcdH0sXG5cdFx0XHRiaWxsaW5nTW9kZTogZHluYW1vZGIuQmlsbGluZ01vZGUuUEFZX1BFUl9SRVFVRVNULFxuXHRcdFx0cG9pbnRJblRpbWVSZWNvdmVyeVNwZWNpZmljYXRpb246IHsgcG9pbnRJblRpbWVSZWNvdmVyeUVuYWJsZWQ6IHRydWUgfSxcblx0XHRcdHJlbW92YWxQb2xpY3k6IGNkay5SZW1vdmFsUG9saWN5LkRFU1RST1ksXG5cdFx0fSk7XG5cblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHQvLyBTZWNyZXRzIE1hbmFnZXJcblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHRjb25zdCBsaW5lQ2hhbm5lbFNlY3JldCA9IG5ldyBzZWNyZXRzbWFuYWdlci5TZWNyZXQoXG5cdFx0XHR0aGlzLFxuXHRcdFx0XCJMaW5lQ2hhbm5lbFNlY3JldFwiLFxuXHRcdFx0e1xuXHRcdFx0XHRzZWNyZXROYW1lOiBcImxpbmUtY2hhbm5lbC1zZWNyZXRcIixcblx0XHRcdFx0ZGVzY3JpcHRpb246IFwiTElORSBDaGFubmVsIFNlY3JldCBmb3Igd2ViaG9vayB2ZXJpZmljYXRpb25cIixcblx0XHRcdH0sXG5cdFx0KTtcblxuXHRcdGNvbnN0IGxpbmVDaGFubmVsQWNjZXNzVG9rZW4gPSBuZXcgc2VjcmV0c21hbmFnZXIuU2VjcmV0KFxuXHRcdFx0dGhpcyxcblx0XHRcdFwiTGluZUNoYW5uZWxBY2Nlc3NUb2tlblwiLFxuXHRcdFx0e1xuXHRcdFx0XHRzZWNyZXROYW1lOiBcImxpbmUtY2hhbm5lbC1hY2Nlc3MtdG9rZW5cIixcblx0XHRcdFx0ZGVzY3JpcHRpb246IFwiTElORSBDaGFubmVsIEFjY2VzcyBUb2tlbiBmb3IgbWVzc2FnaW5nIEFQSVwiLFxuXHRcdFx0fSxcblx0XHQpO1xuXG5cdFx0Y29uc3Qgd2VhdGhlckFwaUtleSA9IG5ldyBzZWNyZXRzbWFuYWdlci5TZWNyZXQoXG5cdFx0XHR0aGlzLFxuXHRcdFx0XCJXZWF0aGVyQXBpS2V5XCIsXG5cdFx0XHR7XG5cdFx0XHRcdHNlY3JldE5hbWU6IFwid2VhdGhlcmFwaS1hcGkta2V5XCIsXG5cdFx0XHRcdGRlc2NyaXB0aW9uOiBcIldlYXRoZXJBUEkgQVBJIEtleSBmb3Igd2VhdGhlciBkYXRhXCIsXG5cdFx0XHR9LFxuXHRcdCk7XG5cblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHQvLyBMYW1iZGEgLSBXZWJob29rIEhhbmRsZXJcblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHRjb25zdCB3ZWJob29rTG9nR3JvdXAgPSBuZXcgbG9ncy5Mb2dHcm91cCh0aGlzLCBcIldlYmhvb2tIYW5kbGVyTG9nR3JvdXBcIiwge1xuXHRcdFx0bG9nR3JvdXBOYW1lOiBcIi9hd3MvbGFtYmRhL3dlYXRoZXItYnJvYWRjYXN0LWxpbmUtd2ViaG9vay1oYW5kbGVyXCIsXG5cdFx0XHRyZXRlbnRpb246IGxvZ3MuUmV0ZW50aW9uRGF5cy5PTkVfTU9OVEgsXG5cdFx0XHRyZW1vdmFsUG9saWN5OiBjZGsuUmVtb3ZhbFBvbGljeS5ERVNUUk9ZLFxuXHRcdH0pO1xuXG5cdFx0Y29uc3QgYXBwQ29kZSA9IGxhbWJkYS5Db2RlLmZyb21Bc3NldChcblx0XHRcdHBhdGguam9pbihfX2Rpcm5hbWUsIFwiLi4vLi4vYXBwXCIpLFxuXHRcdFx0e1xuXHRcdFx0XHRidW5kbGluZzoge1xuXHRcdFx0XHRcdGltYWdlOiBsYW1iZGEuUnVudGltZS5QWVRIT05fM18xMi5idW5kbGluZ0ltYWdlLFxuXHRcdFx0XHRcdGNvbW1hbmQ6IFtcblx0XHRcdFx0XHRcdFwiYmFzaFwiLFxuXHRcdFx0XHRcdFx0XCItY1wiLFxuXHRcdFx0XHRcdFx0XCJwaXAgaW5zdGFsbCAtciByZXF1aXJlbWVudHMudHh0IC10IC9hc3NldC1vdXRwdXQgJiYgcnN5bmMgLWF1IC0tZXhjbHVkZSAnLnZlbnYnIC0tZXhjbHVkZSAnX19weWNhY2hlX18nIC0tZXhjbHVkZSAndGVzdHMnIC0tZXhjbHVkZSAnLmRldmNvbnRhaW5lcicgLS1leGNsdWRlICcqLnB5YycgLS1leGNsdWRlICdweXByb2plY3QudG9tbCcgLS1leGNsdWRlICd1di5sb2NrJyAtLWV4Y2x1ZGUgJ0RvY2tlcmZpbGUnIC0tZXhjbHVkZSAncmVxdWlyZW1lbnRzLnR4dCcgLiAvYXNzZXQtb3V0cHV0XCIsXG5cdFx0XHRcdFx0XSxcblx0XHRcdFx0fSxcblx0XHRcdFx0ZXhjbHVkZTogW1xuXHRcdFx0XHRcdFwiLnZlbnZcIixcblx0XHRcdFx0XHRcIl9fcHljYWNoZV9fXCIsXG5cdFx0XHRcdFx0XCJ0ZXN0c1wiLFxuXHRcdFx0XHRcdFwiLmRldmNvbnRhaW5lclwiLFxuXHRcdFx0XHRcdFwiKi5weWNcIixcblx0XHRcdFx0XHRcInB5cHJvamVjdC50b21sXCIsXG5cdFx0XHRcdFx0XCJ1di5sb2NrXCIsXG5cdFx0XHRcdFx0XCJEb2NrZXJmaWxlXCIsXG5cdFx0XHRcdF0sXG5cdFx0XHR9LFxuXHRcdCk7XG5cblx0XHRjb25zdCB3ZWJob29rSGFuZGxlciA9IG5ldyBsYW1iZGEuRnVuY3Rpb24odGhpcywgXCJMaW5lV2ViaG9va0hhbmRsZXJcIiwge1xuXHRcdFx0ZnVuY3Rpb25OYW1lOiBcIndlYXRoZXItYnJvYWRjYXN0LWxpbmUtd2ViaG9vay1oYW5kbGVyXCIsXG5cdFx0XHRydW50aW1lOiBsYW1iZGEuUnVudGltZS5QWVRIT05fM18xMixcblx0XHRcdGhhbmRsZXI6IFwiaGFuZGxlcnMud2ViaG9vay5oYW5kbGVyXCIsXG5cdFx0XHRjb2RlOiBhcHBDb2RlLFxuXHRcdFx0dGltZW91dDogY2RrLkR1cmF0aW9uLnNlY29uZHMoMzApLFxuXHRcdFx0bWVtb3J5U2l6ZTogMjU2LFxuXHRcdFx0YXJjaGl0ZWN0dXJlOiBsYW1iZGEuQXJjaGl0ZWN0dXJlLlg4Nl82NCxcblx0XHRcdGVudmlyb25tZW50OiB7XG5cdFx0XHRcdFRBQkxFX05BTUU6IHVzZXJzVGFibGUudGFibGVOYW1lLFxuXHRcdFx0XHRMSU5FX0NIQU5ORUxfU0VDUkVUX05BTUU6IGxpbmVDaGFubmVsU2VjcmV0LnNlY3JldE5hbWUsXG5cdFx0XHRcdExJTkVfQ0hBTk5FTF9BQ0NFU1NfVE9LRU5fTkFNRTogbGluZUNoYW5uZWxBY2Nlc3NUb2tlbi5zZWNyZXROYW1lLFxuXHRcdFx0fSxcblx0XHRcdGxvZ0dyb3VwOiB3ZWJob29rTG9nR3JvdXAsXG5cdFx0fSk7XG5cblx0XHQvLyBXZWJob29rIExhbWJkYSBwZXJtaXNzaW9uc1xuXHRcdHVzZXJzVGFibGUuZ3JhbnRSZWFkV3JpdGVEYXRhKHdlYmhvb2tIYW5kbGVyKTtcblx0XHRsaW5lQ2hhbm5lbFNlY3JldC5ncmFudFJlYWQod2ViaG9va0hhbmRsZXIpO1xuXHRcdGxpbmVDaGFubmVsQWNjZXNzVG9rZW4uZ3JhbnRSZWFkKHdlYmhvb2tIYW5kbGVyKTtcblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHQvLyBMYW1iZGEgLSBCcm9hZGNhc3QgSGFuZGxlclxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdGNvbnN0IGJyb2FkY2FzdExvZ0dyb3VwID0gbmV3IGxvZ3MuTG9nR3JvdXAoXG5cdFx0XHR0aGlzLFxuXHRcdFx0XCJCcm9hZGNhc3RIYW5kbGVyTG9nR3JvdXBcIixcblx0XHRcdHtcblx0XHRcdFx0bG9nR3JvdXBOYW1lOiBcIi9hd3MvbGFtYmRhL3dlYXRoZXItYnJvYWRjYXN0LXdlYXRoZXItYnJvYWRjYXN0LWhhbmRsZXJcIixcblx0XHRcdFx0cmV0ZW50aW9uOiBsb2dzLlJldGVudGlvbkRheXMuT05FX01PTlRILFxuXHRcdFx0XHRyZW1vdmFsUG9saWN5OiBjZGsuUmVtb3ZhbFBvbGljeS5ERVNUUk9ZLFxuXHRcdFx0fSxcblx0XHQpO1xuXG5cdFx0Y29uc3QgYnJvYWRjYXN0SGFuZGxlciA9IG5ldyBsYW1iZGEuRnVuY3Rpb24oXG5cdFx0XHR0aGlzLFxuXHRcdFx0XCJXZWF0aGVyQnJvYWRjYXN0SGFuZGxlclwiLFxuXHRcdFx0e1xuXHRcdFx0XHRmdW5jdGlvbk5hbWU6IFwid2VhdGhlci1icm9hZGNhc3Qtd2VhdGhlci1icm9hZGNhc3QtaGFuZGxlclwiLFxuXHRcdFx0XHRydW50aW1lOiBsYW1iZGEuUnVudGltZS5QWVRIT05fM18xMixcblx0XHRcdFx0aGFuZGxlcjogXCJoYW5kbGVycy5icm9hZGNhc3QuaGFuZGxlclwiLFxuXHRcdFx0XHRjb2RlOiBhcHBDb2RlLFxuXHRcdFx0XHR0aW1lb3V0OiBjZGsuRHVyYXRpb24uc2Vjb25kcygzMDApLFxuXHRcdFx0XHRtZW1vcnlTaXplOiA1MTIsXG5cdFx0XHRcdGFyY2hpdGVjdHVyZTogbGFtYmRhLkFyY2hpdGVjdHVyZS5YODZfNjQsXG5cdFx0XHRcdGVudmlyb25tZW50OiB7XG5cdFx0XHRcdFx0VEFCTEVfTkFNRTogdXNlcnNUYWJsZS50YWJsZU5hbWUsXG5cdFx0XHRcdFx0TElORV9DSEFOTkVMX0FDQ0VTU19UT0tFTl9OQU1FOiBsaW5lQ2hhbm5lbEFjY2Vzc1Rva2VuLnNlY3JldE5hbWUsXG5cdFx0XHRcdFx0V0VBVEhFUkFQSV9BUElfS0VZX05BTUU6IHdlYXRoZXJBcGlLZXkuc2VjcmV0TmFtZSxcblx0XHRcdFx0fSxcblx0XHRcdFx0bG9nR3JvdXA6IGJyb2FkY2FzdExvZ0dyb3VwLFxuXHRcdFx0fSxcblx0XHQpO1xuXG5cdFx0Ly8gQnJvYWRjYXN0IExhbWJkYSBwZXJtaXNzaW9uc1xuXHRcdHVzZXJzVGFibGUuZ3JhbnRSZWFkRGF0YShicm9hZGNhc3RIYW5kbGVyKTtcblx0XHRsaW5lQ2hhbm5lbEFjY2Vzc1Rva2VuLmdyYW50UmVhZChicm9hZGNhc3RIYW5kbGVyKTtcblx0XHR3ZWF0aGVyQXBpS2V5LmdyYW50UmVhZChicm9hZGNhc3RIYW5kbGVyKTtcblxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdC8vIEFQSSBHYXRld2F5XG5cdFx0Ly8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG5cdFx0Y29uc3QgYXBpID0gbmV3IGFwaWdhdGV3YXkuUmVzdEFwaSh0aGlzLCBcIldlYmhvb2tBcGlcIiwge1xuXHRcdFx0cmVzdEFwaU5hbWU6IFwid2VhdGhlci1icm9hZGNhc3Qtd2ViaG9vay1hcGlcIixcblx0XHRcdGVuZHBvaW50VHlwZXM6IFthcGlnYXRld2F5LkVuZHBvaW50VHlwZS5SRUdJT05BTF0sXG5cdFx0XHRkZXBsb3lPcHRpb25zOiB7XG5cdFx0XHRcdHN0YWdlTmFtZTogXCJwcm9kXCIsXG5cdFx0XHR9LFxuXHRcdH0pO1xuXG5cdFx0Y29uc3Qgd2ViaG9va1Jlc291cmNlID0gYXBpLnJvb3QuYWRkUmVzb3VyY2UoXCJ3ZWJob29rXCIpO1xuXHRcdHdlYmhvb2tSZXNvdXJjZS5hZGRNZXRob2QoXG5cdFx0XHRcIlBPU1RcIixcblx0XHRcdG5ldyBhcGlnYXRld2F5LkxhbWJkYUludGVncmF0aW9uKHdlYmhvb2tIYW5kbGVyLCB7XG5cdFx0XHRcdHByb3h5OiB0cnVlLFxuXHRcdFx0fSksXG5cdFx0KTtcblxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdC8vIEV2ZW50QnJpZGdlIFNjaGVkdWxlIFJ1bGVcblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHRuZXcgZXZlbnRzLlJ1bGUodGhpcywgXCJXZWF0aGVyQnJvYWRjYXN0U2NoZWR1bGVcIiwge1xuXHRcdFx0cnVsZU5hbWU6IFwid2VhdGhlci1icm9hZGNhc3Qtc2NoZWR1bGVcIixcblx0XHRcdGRlc2NyaXB0aW9uOiBcIlRyaWdnZXIgd2VhdGhlciBicm9hZGNhc3QgYXQgOTowMCBKU1QgZGFpbHlcIixcblx0XHRcdHNjaGVkdWxlOiBldmVudHMuU2NoZWR1bGUuZXhwcmVzc2lvbihcImNyb24oMCAwICogKiA/ICopXCIpLFxuXHRcdFx0ZW5hYmxlZDogdHJ1ZSxcblx0XHRcdHRhcmdldHM6IFtuZXcgdGFyZ2V0cy5MYW1iZGFGdW5jdGlvbihicm9hZGNhc3RIYW5kbGVyKV0sXG5cdFx0fSk7XG5cblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHQvLyBTdGFjayBPdXRwdXRzXG5cdFx0Ly8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG5cdFx0bmV3IGNkay5DZm5PdXRwdXQodGhpcywgXCJXZWJob29rQXBpVXJsXCIsIHtcblx0XHRcdHZhbHVlOiBgJHthcGkudXJsfXdlYmhvb2tgLFxuXHRcdFx0ZGVzY3JpcHRpb246IFwiTElORSBXZWJob29rIFVSTFwiLFxuXHRcdH0pO1xuXG5cdFx0bmV3IGNkay5DZm5PdXRwdXQodGhpcywgXCJVc2Vyc1RhYmxlTmFtZVwiLCB7XG5cdFx0XHR2YWx1ZTogdXNlcnNUYWJsZS50YWJsZU5hbWUsXG5cdFx0XHRkZXNjcmlwdGlvbjogXCJVc2VycyB0YWJsZSBuYW1lXCIsXG5cdFx0fSk7XG5cdH1cbn1cbiJdfQ==