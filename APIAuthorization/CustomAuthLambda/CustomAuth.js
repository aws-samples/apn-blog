
// Modules.
var request = require('request');


// A function to generate a response from Authorizer to API Gateway.
function generate_policy(apiOptions, body, effect, resource) {

  return {

    "principalId": body.email, // the principal user identification associated with the token send by the client
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


// An authorizer implementation
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

  // Introspect if the JWT Token is Valid by calling out to Auth0
  // Validates a JSON Web Token (signature and expiration) and returns the user information associated 
  // TODO: Replace the TokenInfo API URL
  var options = {
    method: 'POST',
    json: true,
    url: 'https://auth0jwtdemo.auth0.com',
    headers: { 'content-type': 'application/json' },
    body: { 'id_token': access_token }
  };

  request(options, function (error, response, body) {
    if (error) throw new Error(error);
    
    console.log("body = " + body);
    console.log("StatusCode = " + response.statusCode);

    // Signature MisMatch or Token expired 401/403. 
    if (body == "Unauthorized") {
      context.succeed(generate_policy(apiOptions, body, 'Deny', event.methodArn));
      console.log("Deny IAM Policy Generated");
    }
    else if (response.statusCode == 200)  // JWT is Valid. Implement additional custom Authorization rules.
    {
      var action = 'Allow';

      if ((apiOptions.resource_path.trim() == 'device' && body.identities[0].provider.trim() == 'amazon') ||
            (apiOptions.resource_path.trim() == 'movie' && body.identities[0].provider.trim() == 'google-oauth2')) {
                action = 'Deny';
      }

      console.log(action + " IAM Policy Generated");
      context.succeed(generate_policy(apiOptions, body, action, event.methodArn));
    }
    else {  //404,500      
      context.succeed(generate_policy(apiOptions, body, 'Deny', event.methodArn));
      console.log("Deny IAM Policy Generated");      
    }
  });

};
