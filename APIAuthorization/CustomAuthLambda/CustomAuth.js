
// Modules.
var request = require('request');
var jwt = require('jsonwebtoken');


// Generate a response from Authorizer to API Gateway.
function generate_policy(apiOptions, sub, effect, resource) {

  return {

    "principalId": sub,
    "policyDocument": {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": effect,
          "Action": [
            "execute-api:Invoke"
          ],
          "Resource": [
            "arn:aws:execute-api:" + apiOptions.region + ":" + apiOptions.awsAccountId + ":" +
            apiOptions.restApiId + "/" + apiOptions.stage + "/" + apiOptions.http_method + "/" + apiOptions.resource_path
          ]
        }
      ]
    }
  };

}



exports.handler = function (event, context) {
  // Get information about the function that is requested to be invoked.
  // Extract the HTTP method and the resource path from event.methodArn.

  console.log("authorizationToken = " + event.authorizationToken);
  console.log("methodArn = " + event.methodArn);

  // parse the ARN from the incoming event
  var apiOptions = {};
  var tmp = event.methodArn.split(':');
  var apiGatewayArnTmp = tmp[5].split('/');
  var arn_elements = event.methodArn.split(':', 6);
  var resource_elements = arn_elements[5].split('/', 4);

  apiOptions.awsAccountId = tmp[4];
  apiOptions.region = tmp[3];
  apiOptions.restApiId = apiGatewayArnTmp[0];
  apiOptions.stage = apiGatewayArnTmp[1];
  apiOptions.http_method = resource_elements[2];
  apiOptions.resource_path = resource_elements[3];

  // The access token presented by the client application.
  var access_token = event.authorizationToken;
  
  //TODO: Replace Signing Secret (Refer to Auth0 API settings)
  var signingSecret = 'ConfigureYourSigningSecret';  

  console.log(access_token);  
  
  //TODO: Replace the audience parameter value
  jwt.verify(access_token, signingSecret, { audience: 'https://StreamingResourceServer', algorithms: '["HS256"]'}, 
   function(err, decoded){

    if (err) {
      console.log('JWT Verification Error');
      console.log(err);  
      console.log(err.message);
      context.succeed(generate_policy(apiOptions, '', 'Deny', event.methodArn));      
    } 
    else {

      console.log(decoded);      
      console.log("Scope = " + decoded.scope);

      if ((decoded.scope == "read:Devices" && apiOptions.resource_path.trim() == 'device') ||
          (decoded.scope == "read:Movies" && apiOptions.resource_path.trim() == 'movie')) {
            context.succeed(generate_policy(apiOptions, decoded.sub, 'Allow', event.methodArn));
            console.log("Allow IAM Policy Generated");
      }
      else {  
        context.succeed(generate_policy(apiOptions, decoded.sub, 'Deny', event.methodArn));
        console.log("Deny IAM Policy Generated");
      }

    }

  });

};
  



