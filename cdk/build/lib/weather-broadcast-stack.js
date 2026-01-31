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
        const openWeatherMapApiKey = new secretsmanager.Secret(this, "OpenWeatherMapApiKey", {
            secretName: "openweathermap-api-key",
            description: "OpenWeatherMap API Key for weather data",
        });
        // =============================================
        // Lambda - Webhook Handler
        // =============================================
        const webhookLogGroup = new logs.LogGroup(this, "WebhookHandlerLogGroup", {
            logGroupName: "/aws/lambda/weather-broadcast-line-webhook-handler",
            retention: logs.RetentionDays.ONE_MONTH,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
        });
        const webhookHandler = new lambda.Function(this, "LineWebhookHandler", {
            functionName: "weather-broadcast-line-webhook-handler",
            runtime: lambda.Runtime.PYTHON_3_12,
            handler: "index.handler",
            code: lambda.Code.fromAsset(path.join(__dirname, "../lambda/webhook")),
            timeout: cdk.Duration.seconds(30),
            memorySize: 256,
            architecture: lambda.Architecture.X86_64,
            environment: {
                TABLE_NAME: usersTable.tableName,
                LINE_CHANNEL_SECRET_NAME: lineChannelSecret.secretName,
                LINE_CHANNEL_ACCESS_TOKEN_NAME: lineChannelAccessToken.secretName,
                OPENWEATHERMAP_API_KEY_NAME: openWeatherMapApiKey.secretName,
            },
            logGroup: webhookLogGroup,
        });
        // Webhook Lambda permissions
        usersTable.grantReadWriteData(webhookHandler);
        lineChannelSecret.grantRead(webhookHandler);
        lineChannelAccessToken.grantRead(webhookHandler);
        openWeatherMapApiKey.grantRead(webhookHandler);
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
            handler: "index.handler",
            code: lambda.Code.fromAsset(path.join(__dirname, "../lambda/broadcast")),
            timeout: cdk.Duration.seconds(300),
            memorySize: 512,
            architecture: lambda.Architecture.X86_64,
            environment: {
                TABLE_NAME: usersTable.tableName,
                LINE_CHANNEL_ACCESS_TOKEN_NAME: lineChannelAccessToken.secretName,
                OPENWEATHERMAP_API_KEY_NAME: openWeatherMapApiKey.secretName,
            },
            logGroup: broadcastLogGroup,
        });
        // Broadcast Lambda permissions
        usersTable.grantReadData(broadcastHandler);
        lineChannelAccessToken.grantRead(broadcastHandler);
        openWeatherMapApiKey.grantRead(broadcastHandler);
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
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoid2VhdGhlci1icm9hZGNhc3Qtc3RhY2suanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi9saWIvd2VhdGhlci1icm9hZGNhc3Qtc3RhY2sudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQUEsa0NBQWtDO0FBQ2xDLG1DQUFtQztBQUNuQyx5REFBeUQ7QUFDekQscURBQXFEO0FBQ3JELGlEQUFpRDtBQUNqRCwwREFBMEQ7QUFDMUQsaURBQWlEO0FBQ2pELDZDQUE2QztBQUM3QyxpRUFBaUU7QUFHakUsTUFBYSxxQkFBc0IsU0FBUSxHQUFHLENBQUMsS0FBSztJQUNuRCxZQUFZLEtBQWdCLEVBQUUsRUFBVSxFQUFFLEtBQXNCO1FBQy9ELEtBQUssQ0FBQyxLQUFLLEVBQUUsRUFBRSxFQUFFLEtBQUssQ0FBQyxDQUFDO1FBRXhCLGdEQUFnRDtRQUNoRCx1QkFBdUI7UUFDdkIsZ0RBQWdEO1FBQ2hELE1BQU0sVUFBVSxHQUFHLElBQUksUUFBUSxDQUFDLEtBQUssQ0FBQyxJQUFJLEVBQUUsWUFBWSxFQUFFO1lBQ3pELFNBQVMsRUFBRSx3QkFBd0I7WUFDbkMsWUFBWSxFQUFFO2dCQUNiLElBQUksRUFBRSxRQUFRO2dCQUNkLElBQUksRUFBRSxRQUFRLENBQUMsYUFBYSxDQUFDLE1BQU07YUFDbkM7WUFDRCxXQUFXLEVBQUUsUUFBUSxDQUFDLFdBQVcsQ0FBQyxlQUFlO1lBQ2pELGdDQUFnQyxFQUFFLEVBQUUsMEJBQTBCLEVBQUUsSUFBSSxFQUFFO1lBQ3RFLGFBQWEsRUFBRSxHQUFHLENBQUMsYUFBYSxDQUFDLE9BQU87U0FDeEMsQ0FBQyxDQUFDO1FBRUgsZ0RBQWdEO1FBQ2hELGtCQUFrQjtRQUNsQixnREFBZ0Q7UUFDaEQsTUFBTSxpQkFBaUIsR0FBRyxJQUFJLGNBQWMsQ0FBQyxNQUFNLENBQ2xELElBQUksRUFDSixtQkFBbUIsRUFDbkI7WUFDQyxVQUFVLEVBQUUscUJBQXFCO1lBQ2pDLFdBQVcsRUFBRSw4Q0FBOEM7U0FDM0QsQ0FDRCxDQUFDO1FBRUYsTUFBTSxzQkFBc0IsR0FBRyxJQUFJLGNBQWMsQ0FBQyxNQUFNLENBQ3ZELElBQUksRUFDSix3QkFBd0IsRUFDeEI7WUFDQyxVQUFVLEVBQUUsMkJBQTJCO1lBQ3ZDLFdBQVcsRUFBRSw2Q0FBNkM7U0FDMUQsQ0FDRCxDQUFDO1FBRUYsTUFBTSxvQkFBb0IsR0FBRyxJQUFJLGNBQWMsQ0FBQyxNQUFNLENBQ3JELElBQUksRUFDSixzQkFBc0IsRUFDdEI7WUFDQyxVQUFVLEVBQUUsd0JBQXdCO1lBQ3BDLFdBQVcsRUFBRSx5Q0FBeUM7U0FDdEQsQ0FDRCxDQUFDO1FBRUYsZ0RBQWdEO1FBQ2hELDJCQUEyQjtRQUMzQixnREFBZ0Q7UUFDaEQsTUFBTSxlQUFlLEdBQUcsSUFBSSxJQUFJLENBQUMsUUFBUSxDQUFDLElBQUksRUFBRSx3QkFBd0IsRUFBRTtZQUN6RSxZQUFZLEVBQUUsb0RBQW9EO1lBQ2xFLFNBQVMsRUFBRSxJQUFJLENBQUMsYUFBYSxDQUFDLFNBQVM7WUFDdkMsYUFBYSxFQUFFLEdBQUcsQ0FBQyxhQUFhLENBQUMsT0FBTztTQUN4QyxDQUFDLENBQUM7UUFFSCxNQUFNLGNBQWMsR0FBRyxJQUFJLE1BQU0sQ0FBQyxRQUFRLENBQUMsSUFBSSxFQUFFLG9CQUFvQixFQUFFO1lBQ3RFLFlBQVksRUFBRSx3Q0FBd0M7WUFDdEQsT0FBTyxFQUFFLE1BQU0sQ0FBQyxPQUFPLENBQUMsV0FBVztZQUNuQyxPQUFPLEVBQUUsZUFBZTtZQUN4QixJQUFJLEVBQUUsTUFBTSxDQUFDLElBQUksQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLElBQUksQ0FBQyxTQUFTLEVBQUUsbUJBQW1CLENBQUMsQ0FBQztZQUN0RSxPQUFPLEVBQUUsR0FBRyxDQUFDLFFBQVEsQ0FBQyxPQUFPLENBQUMsRUFBRSxDQUFDO1lBQ2pDLFVBQVUsRUFBRSxHQUFHO1lBQ2YsWUFBWSxFQUFFLE1BQU0sQ0FBQyxZQUFZLENBQUMsTUFBTTtZQUN4QyxXQUFXLEVBQUU7Z0JBQ1osVUFBVSxFQUFFLFVBQVUsQ0FBQyxTQUFTO2dCQUNoQyx3QkFBd0IsRUFBRSxpQkFBaUIsQ0FBQyxVQUFVO2dCQUN0RCw4QkFBOEIsRUFBRSxzQkFBc0IsQ0FBQyxVQUFVO2dCQUNqRSwyQkFBMkIsRUFBRSxvQkFBb0IsQ0FBQyxVQUFVO2FBQzVEO1lBQ0QsUUFBUSxFQUFFLGVBQWU7U0FDekIsQ0FBQyxDQUFDO1FBRUgsNkJBQTZCO1FBQzdCLFVBQVUsQ0FBQyxrQkFBa0IsQ0FBQyxjQUFjLENBQUMsQ0FBQztRQUM5QyxpQkFBaUIsQ0FBQyxTQUFTLENBQUMsY0FBYyxDQUFDLENBQUM7UUFDNUMsc0JBQXNCLENBQUMsU0FBUyxDQUFDLGNBQWMsQ0FBQyxDQUFDO1FBQ2pELG9CQUFvQixDQUFDLFNBQVMsQ0FBQyxjQUFjLENBQUMsQ0FBQztRQUUvQyxnREFBZ0Q7UUFDaEQsNkJBQTZCO1FBQzdCLGdEQUFnRDtRQUNoRCxNQUFNLGlCQUFpQixHQUFHLElBQUksSUFBSSxDQUFDLFFBQVEsQ0FDMUMsSUFBSSxFQUNKLDBCQUEwQixFQUMxQjtZQUNDLFlBQVksRUFBRSx5REFBeUQ7WUFDdkUsU0FBUyxFQUFFLElBQUksQ0FBQyxhQUFhLENBQUMsU0FBUztZQUN2QyxhQUFhLEVBQUUsR0FBRyxDQUFDLGFBQWEsQ0FBQyxPQUFPO1NBQ3hDLENBQ0QsQ0FBQztRQUVGLE1BQU0sZ0JBQWdCLEdBQUcsSUFBSSxNQUFNLENBQUMsUUFBUSxDQUMzQyxJQUFJLEVBQ0oseUJBQXlCLEVBQ3pCO1lBQ0MsWUFBWSxFQUFFLDZDQUE2QztZQUMzRCxPQUFPLEVBQUUsTUFBTSxDQUFDLE9BQU8sQ0FBQyxXQUFXO1lBQ25DLE9BQU8sRUFBRSxlQUFlO1lBQ3hCLElBQUksRUFBRSxNQUFNLENBQUMsSUFBSSxDQUFDLFNBQVMsQ0FDMUIsSUFBSSxDQUFDLElBQUksQ0FBQyxTQUFTLEVBQUUscUJBQXFCLENBQUMsQ0FDM0M7WUFDRCxPQUFPLEVBQUUsR0FBRyxDQUFDLFFBQVEsQ0FBQyxPQUFPLENBQUMsR0FBRyxDQUFDO1lBQ2xDLFVBQVUsRUFBRSxHQUFHO1lBQ2YsWUFBWSxFQUFFLE1BQU0sQ0FBQyxZQUFZLENBQUMsTUFBTTtZQUN4QyxXQUFXLEVBQUU7Z0JBQ1osVUFBVSxFQUFFLFVBQVUsQ0FBQyxTQUFTO2dCQUNoQyw4QkFBOEIsRUFBRSxzQkFBc0IsQ0FBQyxVQUFVO2dCQUNqRSwyQkFBMkIsRUFBRSxvQkFBb0IsQ0FBQyxVQUFVO2FBQzVEO1lBQ0QsUUFBUSxFQUFFLGlCQUFpQjtTQUMzQixDQUNELENBQUM7UUFFRiwrQkFBK0I7UUFDL0IsVUFBVSxDQUFDLGFBQWEsQ0FBQyxnQkFBZ0IsQ0FBQyxDQUFDO1FBQzNDLHNCQUFzQixDQUFDLFNBQVMsQ0FBQyxnQkFBZ0IsQ0FBQyxDQUFDO1FBQ25ELG9CQUFvQixDQUFDLFNBQVMsQ0FBQyxnQkFBZ0IsQ0FBQyxDQUFDO1FBRWpELGdEQUFnRDtRQUNoRCxjQUFjO1FBQ2QsZ0RBQWdEO1FBQ2hELE1BQU0sR0FBRyxHQUFHLElBQUksVUFBVSxDQUFDLE9BQU8sQ0FBQyxJQUFJLEVBQUUsWUFBWSxFQUFFO1lBQ3RELFdBQVcsRUFBRSwrQkFBK0I7WUFDNUMsYUFBYSxFQUFFLENBQUMsVUFBVSxDQUFDLFlBQVksQ0FBQyxRQUFRLENBQUM7WUFDakQsYUFBYSxFQUFFO2dCQUNkLFNBQVMsRUFBRSxNQUFNO2FBQ2pCO1NBQ0QsQ0FBQyxDQUFDO1FBRUgsTUFBTSxlQUFlLEdBQUcsR0FBRyxDQUFDLElBQUksQ0FBQyxXQUFXLENBQUMsU0FBUyxDQUFDLENBQUM7UUFDeEQsZUFBZSxDQUFDLFNBQVMsQ0FDeEIsTUFBTSxFQUNOLElBQUksVUFBVSxDQUFDLGlCQUFpQixDQUFDLGNBQWMsRUFBRTtZQUNoRCxLQUFLLEVBQUUsSUFBSTtTQUNYLENBQUMsQ0FDRixDQUFDO1FBRUYsZ0RBQWdEO1FBQ2hELDRCQUE0QjtRQUM1QixnREFBZ0Q7UUFDaEQsSUFBSSxNQUFNLENBQUMsSUFBSSxDQUFDLElBQUksRUFBRSwwQkFBMEIsRUFBRTtZQUNqRCxRQUFRLEVBQUUsNEJBQTRCO1lBQ3RDLFdBQVcsRUFBRSw2Q0FBNkM7WUFDMUQsUUFBUSxFQUFFLE1BQU0sQ0FBQyxRQUFRLENBQUMsVUFBVSxDQUFDLG1CQUFtQixDQUFDO1lBQ3pELE9BQU8sRUFBRSxJQUFJO1lBQ2IsT0FBTyxFQUFFLENBQUMsSUFBSSxPQUFPLENBQUMsY0FBYyxDQUFDLGdCQUFnQixDQUFDLENBQUM7U0FDdkQsQ0FBQyxDQUFDO1FBRUgsZ0RBQWdEO1FBQ2hELGdCQUFnQjtRQUNoQixnREFBZ0Q7UUFDaEQsSUFBSSxHQUFHLENBQUMsU0FBUyxDQUFDLElBQUksRUFBRSxlQUFlLEVBQUU7WUFDeEMsS0FBSyxFQUFFLEdBQUcsR0FBRyxDQUFDLEdBQUcsU0FBUztZQUMxQixXQUFXLEVBQUUsa0JBQWtCO1NBQy9CLENBQUMsQ0FBQztRQUVILElBQUksR0FBRyxDQUFDLFNBQVMsQ0FBQyxJQUFJLEVBQUUsZ0JBQWdCLEVBQUU7WUFDekMsS0FBSyxFQUFFLFVBQVUsQ0FBQyxTQUFTO1lBQzNCLFdBQVcsRUFBRSxrQkFBa0I7U0FDL0IsQ0FBQyxDQUFDO0lBQ0osQ0FBQztDQUNEO0FBbktELHNEQW1LQyIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCAqIGFzIHBhdGggZnJvbSBcIm5vZGU6cGF0aFwiO1xuaW1wb3J0ICogYXMgY2RrIGZyb20gXCJhd3MtY2RrLWxpYlwiO1xuaW1wb3J0ICogYXMgYXBpZ2F0ZXdheSBmcm9tIFwiYXdzLWNkay1saWIvYXdzLWFwaWdhdGV3YXlcIjtcbmltcG9ydCAqIGFzIGR5bmFtb2RiIGZyb20gXCJhd3MtY2RrLWxpYi9hd3MtZHluYW1vZGJcIjtcbmltcG9ydCAqIGFzIGV2ZW50cyBmcm9tIFwiYXdzLWNkay1saWIvYXdzLWV2ZW50c1wiO1xuaW1wb3J0ICogYXMgdGFyZ2V0cyBmcm9tIFwiYXdzLWNkay1saWIvYXdzLWV2ZW50cy10YXJnZXRzXCI7XG5pbXBvcnQgKiBhcyBsYW1iZGEgZnJvbSBcImF3cy1jZGstbGliL2F3cy1sYW1iZGFcIjtcbmltcG9ydCAqIGFzIGxvZ3MgZnJvbSBcImF3cy1jZGstbGliL2F3cy1sb2dzXCI7XG5pbXBvcnQgKiBhcyBzZWNyZXRzbWFuYWdlciBmcm9tIFwiYXdzLWNkay1saWIvYXdzLXNlY3JldHNtYW5hZ2VyXCI7XG5pbXBvcnQgdHlwZSB7IENvbnN0cnVjdCB9IGZyb20gXCJjb25zdHJ1Y3RzXCI7XG5cbmV4cG9ydCBjbGFzcyBXZWF0aGVyQnJvYWRjYXN0U3RhY2sgZXh0ZW5kcyBjZGsuU3RhY2sge1xuXHRjb25zdHJ1Y3RvcihzY29wZTogQ29uc3RydWN0LCBpZDogc3RyaW5nLCBwcm9wcz86IGNkay5TdGFja1Byb3BzKSB7XG5cdFx0c3VwZXIoc2NvcGUsIGlkLCBwcm9wcyk7XG5cblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHQvLyBEeW5hbW9EQiBVc2VycyBUYWJsZVxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdGNvbnN0IHVzZXJzVGFibGUgPSBuZXcgZHluYW1vZGIuVGFibGUodGhpcywgXCJVc2Vyc1RhYmxlXCIsIHtcblx0XHRcdHRhYmxlTmFtZTogXCJXZWF0aGVyQnJvYWRjYXN0LVVzZXJzXCIsXG5cdFx0XHRwYXJ0aXRpb25LZXk6IHtcblx0XHRcdFx0bmFtZTogXCJ1c2VySWRcIixcblx0XHRcdFx0dHlwZTogZHluYW1vZGIuQXR0cmlidXRlVHlwZS5TVFJJTkcsXG5cdFx0XHR9LFxuXHRcdFx0YmlsbGluZ01vZGU6IGR5bmFtb2RiLkJpbGxpbmdNb2RlLlBBWV9QRVJfUkVRVUVTVCxcblx0XHRcdHBvaW50SW5UaW1lUmVjb3ZlcnlTcGVjaWZpY2F0aW9uOiB7IHBvaW50SW5UaW1lUmVjb3ZlcnlFbmFibGVkOiB0cnVlIH0sXG5cdFx0XHRyZW1vdmFsUG9saWN5OiBjZGsuUmVtb3ZhbFBvbGljeS5ERVNUUk9ZLFxuXHRcdH0pO1xuXG5cdFx0Ly8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG5cdFx0Ly8gU2VjcmV0cyBNYW5hZ2VyXG5cdFx0Ly8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG5cdFx0Y29uc3QgbGluZUNoYW5uZWxTZWNyZXQgPSBuZXcgc2VjcmV0c21hbmFnZXIuU2VjcmV0KFxuXHRcdFx0dGhpcyxcblx0XHRcdFwiTGluZUNoYW5uZWxTZWNyZXRcIixcblx0XHRcdHtcblx0XHRcdFx0c2VjcmV0TmFtZTogXCJsaW5lLWNoYW5uZWwtc2VjcmV0XCIsXG5cdFx0XHRcdGRlc2NyaXB0aW9uOiBcIkxJTkUgQ2hhbm5lbCBTZWNyZXQgZm9yIHdlYmhvb2sgdmVyaWZpY2F0aW9uXCIsXG5cdFx0XHR9LFxuXHRcdCk7XG5cblx0XHRjb25zdCBsaW5lQ2hhbm5lbEFjY2Vzc1Rva2VuID0gbmV3IHNlY3JldHNtYW5hZ2VyLlNlY3JldChcblx0XHRcdHRoaXMsXG5cdFx0XHRcIkxpbmVDaGFubmVsQWNjZXNzVG9rZW5cIixcblx0XHRcdHtcblx0XHRcdFx0c2VjcmV0TmFtZTogXCJsaW5lLWNoYW5uZWwtYWNjZXNzLXRva2VuXCIsXG5cdFx0XHRcdGRlc2NyaXB0aW9uOiBcIkxJTkUgQ2hhbm5lbCBBY2Nlc3MgVG9rZW4gZm9yIG1lc3NhZ2luZyBBUElcIixcblx0XHRcdH0sXG5cdFx0KTtcblxuXHRcdGNvbnN0IG9wZW5XZWF0aGVyTWFwQXBpS2V5ID0gbmV3IHNlY3JldHNtYW5hZ2VyLlNlY3JldChcblx0XHRcdHRoaXMsXG5cdFx0XHRcIk9wZW5XZWF0aGVyTWFwQXBpS2V5XCIsXG5cdFx0XHR7XG5cdFx0XHRcdHNlY3JldE5hbWU6IFwib3BlbndlYXRoZXJtYXAtYXBpLWtleVwiLFxuXHRcdFx0XHRkZXNjcmlwdGlvbjogXCJPcGVuV2VhdGhlck1hcCBBUEkgS2V5IGZvciB3ZWF0aGVyIGRhdGFcIixcblx0XHRcdH0sXG5cdFx0KTtcblxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdC8vIExhbWJkYSAtIFdlYmhvb2sgSGFuZGxlclxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdGNvbnN0IHdlYmhvb2tMb2dHcm91cCA9IG5ldyBsb2dzLkxvZ0dyb3VwKHRoaXMsIFwiV2ViaG9va0hhbmRsZXJMb2dHcm91cFwiLCB7XG5cdFx0XHRsb2dHcm91cE5hbWU6IFwiL2F3cy9sYW1iZGEvd2VhdGhlci1icm9hZGNhc3QtbGluZS13ZWJob29rLWhhbmRsZXJcIixcblx0XHRcdHJldGVudGlvbjogbG9ncy5SZXRlbnRpb25EYXlzLk9ORV9NT05USCxcblx0XHRcdHJlbW92YWxQb2xpY3k6IGNkay5SZW1vdmFsUG9saWN5LkRFU1RST1ksXG5cdFx0fSk7XG5cblx0XHRjb25zdCB3ZWJob29rSGFuZGxlciA9IG5ldyBsYW1iZGEuRnVuY3Rpb24odGhpcywgXCJMaW5lV2ViaG9va0hhbmRsZXJcIiwge1xuXHRcdFx0ZnVuY3Rpb25OYW1lOiBcIndlYXRoZXItYnJvYWRjYXN0LWxpbmUtd2ViaG9vay1oYW5kbGVyXCIsXG5cdFx0XHRydW50aW1lOiBsYW1iZGEuUnVudGltZS5QWVRIT05fM18xMixcblx0XHRcdGhhbmRsZXI6IFwiaW5kZXguaGFuZGxlclwiLFxuXHRcdFx0Y29kZTogbGFtYmRhLkNvZGUuZnJvbUFzc2V0KHBhdGguam9pbihfX2Rpcm5hbWUsIFwiLi4vbGFtYmRhL3dlYmhvb2tcIikpLFxuXHRcdFx0dGltZW91dDogY2RrLkR1cmF0aW9uLnNlY29uZHMoMzApLFxuXHRcdFx0bWVtb3J5U2l6ZTogMjU2LFxuXHRcdFx0YXJjaGl0ZWN0dXJlOiBsYW1iZGEuQXJjaGl0ZWN0dXJlLlg4Nl82NCxcblx0XHRcdGVudmlyb25tZW50OiB7XG5cdFx0XHRcdFRBQkxFX05BTUU6IHVzZXJzVGFibGUudGFibGVOYW1lLFxuXHRcdFx0XHRMSU5FX0NIQU5ORUxfU0VDUkVUX05BTUU6IGxpbmVDaGFubmVsU2VjcmV0LnNlY3JldE5hbWUsXG5cdFx0XHRcdExJTkVfQ0hBTk5FTF9BQ0NFU1NfVE9LRU5fTkFNRTogbGluZUNoYW5uZWxBY2Nlc3NUb2tlbi5zZWNyZXROYW1lLFxuXHRcdFx0XHRPUEVOV0VBVEhFUk1BUF9BUElfS0VZX05BTUU6IG9wZW5XZWF0aGVyTWFwQXBpS2V5LnNlY3JldE5hbWUsXG5cdFx0XHR9LFxuXHRcdFx0bG9nR3JvdXA6IHdlYmhvb2tMb2dHcm91cCxcblx0XHR9KTtcblxuXHRcdC8vIFdlYmhvb2sgTGFtYmRhIHBlcm1pc3Npb25zXG5cdFx0dXNlcnNUYWJsZS5ncmFudFJlYWRXcml0ZURhdGEod2ViaG9va0hhbmRsZXIpO1xuXHRcdGxpbmVDaGFubmVsU2VjcmV0LmdyYW50UmVhZCh3ZWJob29rSGFuZGxlcik7XG5cdFx0bGluZUNoYW5uZWxBY2Nlc3NUb2tlbi5ncmFudFJlYWQod2ViaG9va0hhbmRsZXIpO1xuXHRcdG9wZW5XZWF0aGVyTWFwQXBpS2V5LmdyYW50UmVhZCh3ZWJob29rSGFuZGxlcik7XG5cblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHQvLyBMYW1iZGEgLSBCcm9hZGNhc3QgSGFuZGxlclxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdGNvbnN0IGJyb2FkY2FzdExvZ0dyb3VwID0gbmV3IGxvZ3MuTG9nR3JvdXAoXG5cdFx0XHR0aGlzLFxuXHRcdFx0XCJCcm9hZGNhc3RIYW5kbGVyTG9nR3JvdXBcIixcblx0XHRcdHtcblx0XHRcdFx0bG9nR3JvdXBOYW1lOiBcIi9hd3MvbGFtYmRhL3dlYXRoZXItYnJvYWRjYXN0LXdlYXRoZXItYnJvYWRjYXN0LWhhbmRsZXJcIixcblx0XHRcdFx0cmV0ZW50aW9uOiBsb2dzLlJldGVudGlvbkRheXMuT05FX01PTlRILFxuXHRcdFx0XHRyZW1vdmFsUG9saWN5OiBjZGsuUmVtb3ZhbFBvbGljeS5ERVNUUk9ZLFxuXHRcdFx0fSxcblx0XHQpO1xuXG5cdFx0Y29uc3QgYnJvYWRjYXN0SGFuZGxlciA9IG5ldyBsYW1iZGEuRnVuY3Rpb24oXG5cdFx0XHR0aGlzLFxuXHRcdFx0XCJXZWF0aGVyQnJvYWRjYXN0SGFuZGxlclwiLFxuXHRcdFx0e1xuXHRcdFx0XHRmdW5jdGlvbk5hbWU6IFwid2VhdGhlci1icm9hZGNhc3Qtd2VhdGhlci1icm9hZGNhc3QtaGFuZGxlclwiLFxuXHRcdFx0XHRydW50aW1lOiBsYW1iZGEuUnVudGltZS5QWVRIT05fM18xMixcblx0XHRcdFx0aGFuZGxlcjogXCJpbmRleC5oYW5kbGVyXCIsXG5cdFx0XHRcdGNvZGU6IGxhbWJkYS5Db2RlLmZyb21Bc3NldChcblx0XHRcdFx0XHRwYXRoLmpvaW4oX19kaXJuYW1lLCBcIi4uL2xhbWJkYS9icm9hZGNhc3RcIiksXG5cdFx0XHRcdCksXG5cdFx0XHRcdHRpbWVvdXQ6IGNkay5EdXJhdGlvbi5zZWNvbmRzKDMwMCksXG5cdFx0XHRcdG1lbW9yeVNpemU6IDUxMixcblx0XHRcdFx0YXJjaGl0ZWN0dXJlOiBsYW1iZGEuQXJjaGl0ZWN0dXJlLlg4Nl82NCxcblx0XHRcdFx0ZW52aXJvbm1lbnQ6IHtcblx0XHRcdFx0XHRUQUJMRV9OQU1FOiB1c2Vyc1RhYmxlLnRhYmxlTmFtZSxcblx0XHRcdFx0XHRMSU5FX0NIQU5ORUxfQUNDRVNTX1RPS0VOX05BTUU6IGxpbmVDaGFubmVsQWNjZXNzVG9rZW4uc2VjcmV0TmFtZSxcblx0XHRcdFx0XHRPUEVOV0VBVEhFUk1BUF9BUElfS0VZX05BTUU6IG9wZW5XZWF0aGVyTWFwQXBpS2V5LnNlY3JldE5hbWUsXG5cdFx0XHRcdH0sXG5cdFx0XHRcdGxvZ0dyb3VwOiBicm9hZGNhc3RMb2dHcm91cCxcblx0XHRcdH0sXG5cdFx0KTtcblxuXHRcdC8vIEJyb2FkY2FzdCBMYW1iZGEgcGVybWlzc2lvbnNcblx0XHR1c2Vyc1RhYmxlLmdyYW50UmVhZERhdGEoYnJvYWRjYXN0SGFuZGxlcik7XG5cdFx0bGluZUNoYW5uZWxBY2Nlc3NUb2tlbi5ncmFudFJlYWQoYnJvYWRjYXN0SGFuZGxlcik7XG5cdFx0b3BlbldlYXRoZXJNYXBBcGlLZXkuZ3JhbnRSZWFkKGJyb2FkY2FzdEhhbmRsZXIpO1xuXG5cdFx0Ly8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG5cdFx0Ly8gQVBJIEdhdGV3YXlcblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHRjb25zdCBhcGkgPSBuZXcgYXBpZ2F0ZXdheS5SZXN0QXBpKHRoaXMsIFwiV2ViaG9va0FwaVwiLCB7XG5cdFx0XHRyZXN0QXBpTmFtZTogXCJ3ZWF0aGVyLWJyb2FkY2FzdC13ZWJob29rLWFwaVwiLFxuXHRcdFx0ZW5kcG9pbnRUeXBlczogW2FwaWdhdGV3YXkuRW5kcG9pbnRUeXBlLlJFR0lPTkFMXSxcblx0XHRcdGRlcGxveU9wdGlvbnM6IHtcblx0XHRcdFx0c3RhZ2VOYW1lOiBcInByb2RcIixcblx0XHRcdH0sXG5cdFx0fSk7XG5cblx0XHRjb25zdCB3ZWJob29rUmVzb3VyY2UgPSBhcGkucm9vdC5hZGRSZXNvdXJjZShcIndlYmhvb2tcIik7XG5cdFx0d2ViaG9va1Jlc291cmNlLmFkZE1ldGhvZChcblx0XHRcdFwiUE9TVFwiLFxuXHRcdFx0bmV3IGFwaWdhdGV3YXkuTGFtYmRhSW50ZWdyYXRpb24od2ViaG9va0hhbmRsZXIsIHtcblx0XHRcdFx0cHJveHk6IHRydWUsXG5cdFx0XHR9KSxcblx0XHQpO1xuXG5cdFx0Ly8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG5cdFx0Ly8gRXZlbnRCcmlkZ2UgU2NoZWR1bGUgUnVsZVxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdG5ldyBldmVudHMuUnVsZSh0aGlzLCBcIldlYXRoZXJCcm9hZGNhc3RTY2hlZHVsZVwiLCB7XG5cdFx0XHRydWxlTmFtZTogXCJ3ZWF0aGVyLWJyb2FkY2FzdC1zY2hlZHVsZVwiLFxuXHRcdFx0ZGVzY3JpcHRpb246IFwiVHJpZ2dlciB3ZWF0aGVyIGJyb2FkY2FzdCBhdCA5OjAwIEpTVCBkYWlseVwiLFxuXHRcdFx0c2NoZWR1bGU6IGV2ZW50cy5TY2hlZHVsZS5leHByZXNzaW9uKFwiY3JvbigwIDAgKiAqID8gKilcIiksXG5cdFx0XHRlbmFibGVkOiB0cnVlLFxuXHRcdFx0dGFyZ2V0czogW25ldyB0YXJnZXRzLkxhbWJkYUZ1bmN0aW9uKGJyb2FkY2FzdEhhbmRsZXIpXSxcblx0XHR9KTtcblxuXHRcdC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuXHRcdC8vIFN0YWNrIE91dHB1dHNcblx0XHQvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cblx0XHRuZXcgY2RrLkNmbk91dHB1dCh0aGlzLCBcIldlYmhvb2tBcGlVcmxcIiwge1xuXHRcdFx0dmFsdWU6IGAke2FwaS51cmx9d2ViaG9va2AsXG5cdFx0XHRkZXNjcmlwdGlvbjogXCJMSU5FIFdlYmhvb2sgVVJMXCIsXG5cdFx0fSk7XG5cblx0XHRuZXcgY2RrLkNmbk91dHB1dCh0aGlzLCBcIlVzZXJzVGFibGVOYW1lXCIsIHtcblx0XHRcdHZhbHVlOiB1c2Vyc1RhYmxlLnRhYmxlTmFtZSxcblx0XHRcdGRlc2NyaXB0aW9uOiBcIlVzZXJzIHRhYmxlIG5hbWVcIixcblx0XHR9KTtcblx0fVxufVxuIl19