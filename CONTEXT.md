models:

x-ai/grok-4-fast
2M context $0.20/M 
input tokens $0.50/M 
output tokens

anthropic/claude-sonnet-4.5
1M context
$3/M input tokens
$15/M output tokens

google/gemini-2.5-pro
1.05M context
$1.25/M input tokens
$10/M output tokens

deepseek/deepseek-chat-v3.1
164K context
$0.20/M input tokens
$0.80/M output tokens

openai/gpt-5
400K context
$1.25/M input tokens
$10/M output tokens

moonshotai/kimi-k2-thinking
262K context
$0.60/M input tokens
$2.50/M output tokens

qwen/qwen3-max
256K context
$1.20/M input tokens
$6/M output tokens






docs on parameters: 




---
title: Parameters
headline: API Parameters | Configure OpenRouter API Requests
canonical-url: 'https://openrouter.ai/docs/api-reference/parameters'
'og:site_name': OpenRouter Documentation
'og:title': API Parameters - Complete Guide to Request Configuration
'og:description': >-
  Learn about all available parameters for OpenRouter API requests. Configure
  temperature, max tokens, top_p, and other model-specific settings.
'og:image':
  type: url
  value: >-
    https://openrouter.ai/dynamic-og?title=API%20Parameters&description=Complete%20guide%20to%20request%20configuration
'og:image:width': 1200
'og:image:height': 630
'twitter:card': summary_large_image
'twitter:site': '@OpenRouterAI'
noindex: false
nofollow: false
---

Sampling parameters shape the token generation process of the model. You may send any parameters from the following list, as well as others, to OpenRouter.

OpenRouter will default to the values listed below if certain parameters are absent from your request (for example, `temperature` to 1.0). We will also transmit some provider-specific parameters, such as `safe_prompt` for Mistral or `raw_mode` for Hyperbolic directly to the respective providers if specified.

Please refer to the model’s provider section to confirm which parameters are supported. For detailed guidance on managing provider-specific parameters, [click here](/docs/features/provider-routing#requiring-providers-to-support-all-parameters-beta).

## Temperature

- Key: `temperature`

- Optional, **float**, 0.0 to 2.0

- Default: 1.0

- Explainer Video: [Watch](https://youtu.be/ezgqHnWvua8)

This setting influences the variety in the model's responses. Lower values lead to more predictable and typical responses, while higher values encourage more diverse and less common responses. At 0, the model always gives the same response for a given input.

## Top P

- Key: `top_p`

- Optional, **float**, 0.0 to 1.0

- Default: 1.0

- Explainer Video: [Watch](https://youtu.be/wQP-im_HInk)

This setting limits the model's choices to a percentage of likely tokens: only the top tokens whose probabilities add up to P. A lower value makes the model's responses more predictable, while the default setting allows for a full range of token choices. Think of it like a dynamic Top-K.

## Top K

- Key: `top_k`

- Optional, **integer**, 0 or above

- Default: 0

- Explainer Video: [Watch](https://youtu.be/EbZv6-N8Xlk)

This limits the model's choice of tokens at each step, making it choose from a smaller set. A value of 1 means the model will always pick the most likely next token, leading to predictable results. By default this setting is disabled, making the model to consider all choices.

## Frequency Penalty

- Key: `frequency_penalty`

- Optional, **float**, -2.0 to 2.0

- Default: 0.0

- Explainer Video: [Watch](https://youtu.be/p4gl6fqI0_w)

This setting aims to control the repetition of tokens based on how often they appear in the input. It tries to use less frequently those tokens that appear more in the input, proportional to how frequently they occur. Token penalty scales with the number of occurrences. Negative values will encourage token reuse.

## Presence Penalty

- Key: `presence_penalty`

- Optional, **float**, -2.0 to 2.0

- Default: 0.0

- Explainer Video: [Watch](https://youtu.be/MwHG5HL-P74)

Adjusts how often the model repeats specific tokens already used in the input. Higher values make such repetition less likely, while negative values do the opposite. Token penalty does not scale with the number of occurrences. Negative values will encourage token reuse.

## Repetition Penalty

- Key: `repetition_penalty`

- Optional, **float**, 0.0 to 2.0

- Default: 1.0

- Explainer Video: [Watch](https://youtu.be/LHjGAnLm3DM)

Helps to reduce the repetition of tokens from the input. A higher value makes the model less likely to repeat tokens, but too high a value can make the output less coherent (often with run-on sentences that lack small words). Token penalty scales based on original token's probability.

## Min P

- Key: `min_p`

- Optional, **float**, 0.0 to 1.0

- Default: 0.0

Represents the minimum probability for a token to be
  considered, relative to the probability of the most likely token. (The value changes depending on the confidence level of the most probable token.) If your Min-P is set to 0.1, that means it will only allow for tokens that are at least 1/10th as probable as the best possible option.

## Top A

- Key: `top_a`

- Optional, **float**, 0.0 to 1.0

- Default: 0.0

Consider only the top tokens with "sufficiently high" probabilities based on the probability of the most likely token. Think of it like a dynamic Top-P. A lower Top-A value focuses the choices based on the highest probability token but with a narrower scope. A higher Top-A value does not necessarily affect the creativity of the output, but rather refines the filtering process based on the maximum probability.

## Seed

- Key: `seed`

- Optional, **integer**

If specified, the inferencing will sample deterministically, such that repeated requests with the same seed and parameters should return the same result. Determinism is not guaranteed for some models.

## Max Tokens

- Key: `max_tokens`

- Optional, **integer**, 1 or above

This sets the upper limit for the number of tokens the model can generate in response. It won't produce more than this limit. The maximum value is the context length minus the prompt length.

## Logit Bias

- Key: `logit_bias`

- Optional, **map**

Accepts a JSON object that maps tokens (specified by their token ID in the tokenizer) to an associated bias value from -100 to 100. Mathematically, the bias is added to the logits generated by the model prior to sampling. The exact effect will vary per model, but values between -1 and 1 should decrease or increase likelihood of selection; values like -100 or 100 should result in a ban or exclusive selection of the relevant token.

## Logprobs

- Key: `logprobs`

- Optional, **boolean**

Whether to return log probabilities of the output tokens or not. If true, returns the log probabilities of each output token returned.

## Top Logprobs

- Key: `top_logprobs`

- Optional, **integer**

An integer between 0 and 20 specifying the number of most likely tokens to return at each token position, each with an associated log probability. logprobs must be set to true if this parameter is used.

## Response Format

- Key: `response_format`

- Optional, **map**

Forces the model to produce specific output format. Setting to `{ "type": "json_object" }` enables JSON mode, which guarantees the message the model generates is valid JSON.

  **Note**: when using JSON mode, you should also instruct the model to produce JSON yourself via a system or user message.

## Structured Outputs

- Key: `structured_outputs`

- Optional, **boolean**

If the model can return structured outputs using response_format json_schema.

## Stop

- Key: `stop`

- Optional, **array**

Stop generation immediately if the model encounter any token specified in the stop array.

## Tools

- Key: `tools`

- Optional, **array**

Tool calling parameter, following OpenAI's tool calling request shape. For non-OpenAI providers, it will be transformed accordingly. [Click here to learn more about tool calling](/docs/requests#tool-calls)

## Tool Choice

- Key: `tool_choice`

- Optional, **array**

Controls which (if any) tool is called by the model. 'none' means the model will not call any tool and instead generates a message. 'auto' means the model can pick between generating a message or calling one or more tools. 'required' means the model must call one or more tools. Specifying a particular tool via `{"type": "function", "function": {"name": "my_function"}}` forces the model to call that tool.

## Parallel Tool Calls

- Key: `parallel_tool_calls`

- Optional, **boolean**

- Default: **true**

Whether to enable parallel function calling during tool use. If true, the model can call multiple functions simultaneously. If false, functions will be called sequentially. Only applies when tools are provided.

## Verbosity

- Key: `verbosity`

- Optional, **enum** (low, medium, high)

- Default: **medium**

Controls the verbosity and length of the model response. Lower values produce more concise responses, while higher values produce more detailed and comprehensive responses.








# Get a model's supported parameters and data about which are most popular

GET https://openrouter.ai/api/v1/parameters/{author}/{slug}

Reference: https://openrouter.ai/docs/api-reference/parameters/get-parameters

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get a model's supported parameters and data about which are most popular
  version: endpoint_parameters.getParameters
paths:
  /parameters/{author}/{slug}:
    get:
      operationId: get-parameters
      summary: Get a model's supported parameters and data about which are most popular
      tags:
        - - subpackage_parameters
      parameters:
        - name: author
          in: path
          required: true
          schema:
            type: string
        - name: slug
          in: path
          required: true
          schema:
            type: string
        - name: provider
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/ParametersAuthorSlugGetParametersProvider'
        - name: Authorization
          in: header
          description: API key as bearer token in Authorization header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Returns the parameters for the specified model
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Parameters_getParameters_Response_200'
        '401':
          description: Unauthorized - Authentication required or invalid credentials
          content: {}
        '404':
          description: Not Found - Model or provider does not exist
          content: {}
        '500':
          description: Internal Server Error - Unexpected server error
          content: {}
components:
  schemas:
    ParametersAuthorSlugGetParametersProvider:
      type: string
      enum:
        - value: AI21
        - value: AionLabs
        - value: Alibaba
        - value: Amazon Bedrock
        - value: Anthropic
        - value: AtlasCloud
        - value: Atoma
        - value: Avian
        - value: Azure
        - value: BaseTen
        - value: Cerebras
        - value: Chutes
        - value: Cirrascale
        - value: Clarifai
        - value: Cloudflare
        - value: Cohere
        - value: CrofAI
        - value: Crusoe
        - value: DeepInfra
        - value: DeepSeek
        - value: Enfer
        - value: Featherless
        - value: Fireworks
        - value: Friendli
        - value: GMICloud
        - value: Google
        - value: Google AI Studio
        - value: Groq
        - value: Hyperbolic
        - value: Inception
        - value: InferenceNet
        - value: Infermatic
        - value: Inflection
        - value: Kluster
        - value: Lambda
        - value: Liquid
        - value: Mancer 2
        - value: Meta
        - value: Minimax
        - value: ModelRun
        - value: Mistral
        - value: Modular
        - value: Moonshot AI
        - value: Morph
        - value: NCompass
        - value: Nebius
        - value: NextBit
        - value: Nineteen
        - value: Novita
        - value: Nvidia
        - value: OpenAI
        - value: OpenInference
        - value: Parasail
        - value: Perplexity
        - value: Phala
        - value: Relace
        - value: SambaNova
        - value: SiliconFlow
        - value: Stealth
        - value: Switchpoint
        - value: Targon
        - value: Together
        - value: Ubicloud
        - value: Venice
        - value: WandB
        - value: xAI
        - value: Z.AI
        - value: FakeProvider
    ParametersAuthorSlugGetResponsesContentApplicationJsonSchemaDataSupportedParametersItems:
      type: string
      enum:
        - value: temperature
        - value: top_p
        - value: top_k
        - value: min_p
        - value: top_a
        - value: frequency_penalty
        - value: presence_penalty
        - value: repetition_penalty
        - value: max_tokens
        - value: logit_bias
        - value: logprobs
        - value: top_logprobs
        - value: seed
        - value: response_format
        - value: structured_outputs
        - value: stop
        - value: tools
        - value: tool_choice
        - value: parallel_tool_calls
        - value: include_reasoning
        - value: reasoning
        - value: web_search_options
        - value: verbosity
    ParametersAuthorSlugGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        model:
          type: string
        supported_parameters:
          type: array
          items:
            $ref: >-
              #/components/schemas/ParametersAuthorSlugGetResponsesContentApplicationJsonSchemaDataSupportedParametersItems
      required:
        - model
        - supported_parameters
    Parameters_getParameters_Response_200:
      type: object
      properties:
        data:
          $ref: >-
            #/components/schemas/ParametersAuthorSlugGetResponsesContentApplicationJsonSchemaData
      required:
        - data

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/parameters/author/slug"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/parameters/author/slug';
const options = {method: 'GET', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/parameters/author/slug"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/parameters/author/slug")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/parameters/author/slug")
  .header("Authorization", "Bearer <token>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/parameters/author/slug', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/parameters/author/slug");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/parameters/author/slug")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```




