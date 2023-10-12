# Integration testing with Hurl
## Prerequisites
- Install [just](https://github.com/casey/just)
- Install [Hurl](https://hurl.dev/)

## Usage
- Copy `.env.examaple` to `.env` and update the `OPS_API_KEY` to match the one used in the `.env` file in the `api/` directory.
- Start the API (e.g. by using `just run` from the root directory) and ensure that there is at least one user in the database (the easiest way would be to also start the frontend and log in via the SSO).
- Run the tests: `just test` (or `cd` into the `test` directory and use `hurl --test --variables-file=.env admin_routes.hurl`)