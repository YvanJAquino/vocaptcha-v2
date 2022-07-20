#! /bin/bash

curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d @generate_add_two_numbers.json \
    localhost:8082/add-two-numbers/generate \
    | jq

curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d @generate_nato_passphrase.json \
    localhost:8082/nato-alphabet/generate \
    | jq

curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d @generate_sentences.json \
    localhost:8082/sentences/generate \
    | jq

curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d @verify_add_two_numbers.json \
    localhost:8082/add-two-numbers/verify \
    | jq

curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d @verify_sentences-1.json \
    localhost:8082/sentences/verify \
    | jq

curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d @verify_sentences-2.json \
    localhost:8082/sentences/verify \
    | jq

curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d @verify_nato_passphrase.json \
    localhost:8082/nato-alphabet/verify \
    | jq