targetScope = 'subscription'

// The main bicep module to provision Azure resources.
// For a more complete walkthrough to understand how this file works with azd,
// see https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/make-azd-compatible?pivots=azd-create

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Container Registry image name for the backend app')
param backendImageName string

@description('Container Registry image name for the frontend app')
param frontendImageName string

// Optional parameters to override the default azd resource naming conventions.
// Add the following to main.parameters.json to provide values:
// "resourceGroupName": {
//      "value": "myGroupName"
// }
param resourceGroupName string = ''

var abbrs = loadJsonContent('./abbreviations.json')

// tags that should be applied to all resources.
var tags = {
  // Tag all resources with the environment name.
  'azd-env-name': environmentName
}

// Generate a unique token to be used in naming resources.
// Remove linter suppression after using.
#disable-next-line no-unused-vars
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Name of the service defined in azure.yaml
// A tag named azd-service-name with this value should be applied to the service host resource, such as:
//   Microsoft.Web/sites for appservice, function
// Example usage:
//   tags: union(tags, { 'azd-service-name': apiServiceName })
#disable-next-line no-unused-vars
var apiServiceName = 'python-api'

// Organize resources in a resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

var prefix = '${environmentName}-${resourceToken}'

// Container apps host (including container registry)
module containerApps 'core/host/container-apps.bicep' = {
  name: 'container-apps'
  scope: resourceGroup
  params: {
    name: 'app'
    location: location
    tags: tags
    containerAppsEnvironmentName: '${prefix}-containerapps-env'
    logAnalyticsWorkspaceName: logAnalyticsWorkspace.outputs.name
  }
}

// backend app
module backend 'aca-app.bicep' = {
  name: 'backend'
  scope: resourceGroup
  params: {
    name: replace('${take(prefix,19)}-backend', '--', '-')
    location: location
    tags: tags
    containerAppsEnvironmentName: containerApps.outputs.environmentName
    imageName: backendImageName
    targetPort: 3000
    serviceName: 'backend'
  }
}

// frontend app
module frontend 'aca-app.bicep' = {
  name: 'frontend'
  scope: resourceGroup
  params: {
    name: replace('${take(prefix,19)}-frontend', '--', '-')
    location: location
    tags: tags
    containerAppsEnvironmentName: containerApps.outputs.environmentName
    imageName: frontendImageName
    targetPort: 3000
    env: [
      {
        name: 'backendUri'
        value: 'https://${backend.outputs.SERVICE_API_URI}/api'
      }
    ]
    serviceName: 'frontend'
  }
}

module logAnalyticsWorkspace 'core/monitor/loganalytics.bicep' = {
  name: 'loganalytics'
  scope: resourceGroup
  params: {
    name: '${prefix}-loganalytics'
    location: location
    tags: tags
  }
}

output AZURE_LOCATION string = location
output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerApps.outputs.environmentName
// output AZURE_CONTAINER_REGISTRY_NAME string = containerApps.outputs.registryName
// output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerApps.outputs.registryLoginServer
// output SERVICE_API_IDENTITY_PRINCIPAL_ID string = api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
output SERVICE_BACKEND_NAME string = backend.outputs.SERVICE_API_NAME
output SERVICE_BACKEND_URI string = backend.outputs.SERVICE_API_URI
output SERVICE_BACKEND_IMAGE_NAME string = backend.outputs.SERVICE_API_IMAGE_NAME
output SERVICE_BACKEND_ENDPOINTS array = ['${backend.outputs.SERVICE_API_URI}/api']
output SERVICE_FRONTEND_NAME string = frontend.outputs.SERVICE_API_NAME
output SERVICE_FRONTEND_URI string =frontend.outputs.SERVICE_API_URI
output SERVICE_FRONTEND_IMAGE_NAME string = frontend.outputs.SERVICE_API_IMAGE_NAME
output SERVICE_FRONTEND_ENDPOINTS array = ['${frontend.outputs.SERVICE_API_URI}']
