param name string
param location string = resourceGroup().location
param tags object = {}

param containerAppsEnvironmentName string
param imageName string
param serviceName string

module app 'core/host/container-app-upsert.bicep' = {
  name: '${serviceName}-container-app-module'
  params: {
    name: name
    location: location
    tags: union(tags, { 'azd-service-name': serviceName })
    imageName: imageName
    containerAppsEnvironmentName: containerAppsEnvironmentName
    targetPort: 3100
  }
}

output SERVICE_API_NAME string = app.outputs.name
output SERVICE_API_URI string = app.outputs.uri
output SERVICE_API_IMAGE_NAME string = app.outputs.imageName
