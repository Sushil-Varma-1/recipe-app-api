# recipe-app-api
Food recipes API that returns the recipe and ingredients for the specified meals.

# How to Use
-  Install Python and docker on your system.
-  Clone the project
-  Run "docker-compose build" to create docker container with all the dependencies.
-  Run "docker-compose up" in terminal to run a project.

### Endpoint Usage
---
| Endpoint | Function|
| ------------- | ------------- |
| GET /api/user/me/  |  Get logged in user|
| GET /api/user/create/  |  Create new user|
| POST /api/user/token/  |  Get Bearer Token for authorization |
| PATCH /api/user/me/  |  Update user details |
| GET /api/recipe/recipes/ | Get all the recipes for current user|
| POST /api/recipe/recipes/ | Create a recipe for current user|
| GET /api/recipe/recipes/{id}/ | Get recipe by id for current user|
| PATCH /api/recipe/recipes/{id}/ | Update recipe by id for current user|
| PUT /api/recipe/recipes/{id}/ | Update recipe by id for current user|
| DELETE /api/recipe/recipes/{id}/ | Delete a recipe by id for current user|
| GET /api/recipe/tags/ | Get all the tags created by current user|
| PATCH /api/recipe/tags/{id}/ | Update a tag by id for current user|
| DELETE /api/recipe/tags/{id}/ | Delete a tag by id for current user|
| GET /api/recipe/ingredients/ | Get all the ingredients created by current user|
| PATCH /api/recipe/ingredients/{id}/ | Update the ingredient by id current user|
| DELETE /api/recipe/ingredients/{id}/ | Delete the ingredient by id current user|
