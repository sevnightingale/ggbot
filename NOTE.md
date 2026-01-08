Standard e-commerce flow for NOWPayments API:
API - Check API availability with the "GET API status" method. If required, check the list of available payment currencies with the "GET available currencies" method;

UI - Ask a customer to select item/items for purchase to determine the total sum;

UI - Ask a customer to select payment currency;

API - Get the minimum payment amount for the selected currency pair (payment currency to your payout wallet currency) with the "GET Minimum payment amount" method;

API - Get the estimate of the total amount in crypto with "GET Estimated price" and check that it is larger than the minimum payment amount from step 4;

API - Call the "POST Create payment" method to create a payment and get the deposit address (in our example, the generated BTC wallet address is returned from this method);

UI - Ask a customer to send the payment to the generated deposit address (in our example, user has to send BTC coins);

UI - A customer sends coins, NOWPayments processes and exchanges them (if required), and settles the payment to your payout wallet (in our example, to your ETH address);

API - You can get the payment status either via our IPN callbacks or manually, using "GET Payment Status" and display it to a customer so that they know when their payment has been processed;

API - you call the list of payments made to your account via the "GET List of payments" method;

Additionally, you can see all of this information in your Account on NOWPayments website;

Alternative flow
API - Check API availability with the "GET API status" method. If required, check the list of available payment currencies with the "GET available currencies" method;

UI - Ask a customer to select item/items for purchase to determine the total sum;

UI - Ask a customer to select payment currency;

API - Get the minimum payment amount for the selected currency pair (payment currency to your payout wallet currency) with the "GET Minimum payment amount" method;

API - Get the estimate of the total amount in crypto with "GET Estimated price" and check that it is larger than the minimum payment amount from step 4;

API - Call the "POST Create Invoice method to create an invoice. Set "success_url" - parameter so that the user will be redirected to your website after successful payment;

UI - display the invoice url or redirect the user to the generated link;

NOWPayments - the customer completes the payment and is redirected back to your website (only if "success_url" parameter is configured correctly!);

API - You can get the payment status either via our IPN callbacks or manually, using "GET Payment Status" and display it to a customer so that they know when their payment has been processed;

API - you call the list of payments made to your account via the "GET List of payments" method;

Additionally, you can see all of this information in your Account on NOWPayments website;

API Documentation
Instant Payments Notifications
IPN (Instant payment notifications, or callbacks) are used to notify you when transaction status is changed.
To use them, you should complete the following steps:

Generate and save the IPN Secret key in Payment Settings tab at the Dashboard;

Insert your URL address where you want to get callbacks in create_payment request. The parameter name is ipn_callback_url. You will receive payment updates (statuses) to this URL address.**
Please, take note that we cannot send callbacks to your localhost unless it has dedicated IP address.**

important Please make sure that firewall software on your server (i.e. Cloudflare) does allow our requests to come through. It may be required to whitelist our IP addresses on your side to get it. The list of these IP addresses can be requested at partners@nowpayments.io;

You will receive all the parameters at the URL address you specified in (2) by POST request;
The POST request will contain the x-nowpayments-sig parameter in the header.
The body of the request is similiar to a get payment status response body.
You can see examples in "Webhook examples" section.

Sort the POST request by keys and convert it to string using
JSON.stringify (params, Object.keys(params).sort()) or the same function;

Sign a string with an IPN-secret key with HMAC and sha-512 key;

Compare the signed string from the previous step with the x-nowpayments-sig , which is stored in the header of the callback request;
If these strings are similar, it is a success.
Otherwise, contact us on support@nowpayments.io to solve the problem.

Example of creating a signed string at Node.JS

View More
Plain Text
function sortObject(obj) {
  return Object.keys(obj).sort().reduce(
    (result, key) => {
      result[key] = (obj[key] && typeof obj[key] === 'object') ? sortObject(obj[key]) : obj[key]
      return result
    },
    {}
  )
}
const hmac = crypto.createHmac('sha512', notificationsKey);
hmac.update(JSON.stringify(sortObject(params)));
const signature = hmac.digest('hex');
Example of comparing signed strings in PHP

View More
Plain Text
function tksort(&$array)
  {
  ksort($array);
  foreach(array_keys($array) as $k)
    {
    if(gettype($array[$k])=="array")
      {
      tksort($array[$k]);
      }
    }
  }
function check_ipn_request_is_valid()
    {
        $error_msg = "Unknown error";
        $auth_ok = false;
        $request_data = null;
        if (isset($_SERVER['HTTP_X_NOWPAYMENTS_SIG']) && !empty($_SERVER['HTTP_X_NOWPAYMENTS_SIG'])) {
            $recived_hmac = $_SERVER['HTTP_X_NOWPAYMENTS_SIG'];
            $request_json = file_get_contents('php://input');
            $request_data = json_decode($request_json, true);
            tksort($request_data);
            $sorted_request_json = json_encode($request_data, JSON_UNESCAPED_SLASHES);
            if ($request_json !== false && !empty($request_json)) {
                $hmac = hash_hmac("sha512", $sorted_request_json, trim($this->ipn_secret));
                if ($hmac == $recived_hmac) {
                    $auth_ok = true;
                } else {
                    $error_msg = 'HMAC signature does not match';
                }
            } else {
                $error_msg = 'Error reading POST data';
            }
        } else {
            $error_msg = 'No HMAC signature sent.';
        }
    }
Example comparing signed signatures in Python

View More
python
import json 
import hmac 
import hashlib
def np_signature_check(np_secret_key, np_x_signature, message):
    sorted_msg = json.dumps(message, separators=(',', ':'), sort_keys=True)
    digest = hmac.new(
    str(np_secret_key).encode(), 
    f'{sorted_msg}'.encode(),
    hashlib.sha512)
    signature = digest.hexdigest()
    if signature == np_x_signature:
        return
    else:
        print("HMAC signature does not match")
Usually you will get a notification per each step of processing payments, withdrawals, or transfers, related to custodial recurring payments.

The webhook is being sent automatically once the transaction status is changed.

You also can request an additional IPN notification using your NOWPayments dashboard.

Please note that you should set up an endpoint which can receive POST requests from our server.

Before going production we strongly recommend to make a test request to this endpoint to ensure it works properly.

Recurrent payment notifications
If an error is detected, the payment will be flagged and will receive additional recurrent notifications (number of recurrent notifications can be changed in your Payment Settings-> Instant Payment Notifications).

If an error is received again during the payment processing, recurrent notifications will be initiated again.

Example: "Timeout" is set to 1 minute and "Number of recurrent notifications" is set to 3.

Once an error is detected, you will receive 3 notifications at 1 minute intervals.

Webhooks Examples:
Payments:

View More
json
{
"payment_id":123456789,
"parent_payment_id":987654321,
"invoice_id":null,
"payment_status":"finished",
"pay_address":"address",
"payin_extra_id":null,
"price_amount":1,
"price_currency":"usd",
"pay_amount":15,
"actually_paid":15,
"actually_paid_at_fiat":0,
"pay_currency":"trx",
"order_id":null,
"order_description":null,
"purchase_id":"123456789",
"outcome_amount":14.8106,
"outcome_currency":"trx",
"payment_extra_ids":null
"fee": {
"currency":"btc",
"depositFee":0.09853637216235617,
"withdrawalFee":0,
"serviceFee":0
}
}
Withdrawals:

View More
json
{
"id":"123456789",
"batch_withdrawal_id":"987654321",
"status":"CREATING",
"error":null,
"currency":"usdttrc20",
"amount":"50",
"address":"address",
"fee":null,
"extra_id":null,
"hash":null,
"ipn_callback_url":"callback_url",
"created_at":"2023-07-27T15:29:40.803Z",
"requested_at":null,
"updated_at":null
}
Custodial recurring payments:

json
{
"id":"1234567890",
"status":"FINISHED",
"currency":"trx",
"amount":"12.171365564140688",
"ipn_callback_url":"callback_url",
"created_at":"2023-07-26T14:20:11.531Z",
"updated_at":"2023-07-26T14:20:21.079Z"
}
Repeated Deposits and Wrong-Asset Deposits
This section explains how we handle two specific types of deposits: repeated deposits (re-deposits) and wrong-asset deposits. These deposits may require special processing or manual intervention, and understanding how they work will help you manage your payments more effectively.

Repeated Deposits
Repeated deposits are additional payments sent to the same deposit address that was previously used by a customer to fully or partially pay an invoice. These deposits are processed at the current exchange rate at the time they are received. They are marked with either the "Partially paid" or "Finished" status. If you need to clarify your current repeated-deposit settings, please check with your payment provider regarding the default status.

In the Payments History section of the personal account, these payments are labeled as "Re-deposit". Additionally, in the payment details, the Original payment ID field will display the ID of the original transaction.

Recommendation:

Recommendation: When integrating, we recommend tracking the 'parent_payment_id' parameter in Instant Payment Notifications and being aware that the total amount of repeated deposits may differ from the expected payment amount. This helps avoid the risk of providing services in cases of underpayment.
We do not recommend configuring your system to automatically provide services or ship goods based on any repeated-deposit status. If you choose to configure it this way, you should be aware of the risk of providing services in cases of underpayment. For additional risk acceptance please refer to section 6 of our Terms of Service.

NB: Repeated deposits are always converted to the same asset as the original payment.
Note: To review the current flow or change the default status of repeated payments to "Finished" or "Partially paid", please contact us at support@nowpayments.io.

2. Wrong-Asset Deposits

Wrong-asset deposits occur when a payment is sent using the wrong network or asset (e.g. a user may mistakenly send USDTERC20 instead of ETH), and this network and asset are supported by our service.

These payments will appear in the Payments History section with the label "Wrong Asset" and, by default, will require manual intervention to resolve.

Recommendation: When integrating, we recommend configuring your system to check the amount, asset type and the 'parent_payment_id' param in Instant Payment Notifications of the incoming deposit to avoid the risks of providing services in case of insufficient funds.

If you want wrong-asset deposits to be processed automatically, you can enable the Wrong-Asset Deposits Auto-Processing option in your account settings (Settings -> Payment -> Payment details). Before enabling this option, please take into account that the final sum of the sent deposit may differ from the expected payment amount and by default these payments always receive "Finished" status.

If needed, we can also provide an option to assign a "partially paid" status to deposits processed through this feature. For more details, please contact support@nowpayments.io

Packages
Please find our out-of-the box packages for easy integration below:

JavaScript package

[PHP package]
(https://packagist.org/packages/nowpayments/nowpayments-api-php)

More coming soon!

Payments
POST
Create conversion
https://api.nowpayments.io/v1/conversion
This endpoint allows you to create conversions within your custody account.

Parameters:

amount(required) - the amount of your conversion;
from_currency(required) - the currency you're converting your funds from;
to_currency(required) - the currency you're converting your funds to;
The list of available statuses:

WAITING - the conversion is created and waiting to be executed;
PROCESSING - the conversion is in processing;
FINISHED - the conversion is completed;
REJECTED - for some reason, conversion failed;
HEADERS
Authorization
Bearer {{token}}

(Required) Your authorization token

Content-Type
application/json

(Required) Your payload has to be JSON object

Body
raw
{
    "amount": 50,
    "from_currency": "usdttrc20",
    "to_currency": "USDTERC20"
}
Example Request
200
curl
curl --location --request GET 'https://api.nowpayments.io/v1/conversion' \
--header 'Authorization: Bearer {{token}}' \
--header 'Content-Type: application/json' \
--data '{
    "amount": "50",
    "from_currency": "usdttrc20",
    "to_currency": "USDTERC20"
}'
Example Response
Body
Headers (0)
View More
{
  "result": {
    "id": "1327866232",
    "status": "WAITING",
    "from_currency": "USDTTRC20",
    "to_currency": "USDTERC20",
    "from_amount": 50,
    "to_amount": 50,
    "created_at": "2023-03-05T08:18:30.384Z",
    "updated_at": "2023-03-05T08:18:30.384Z"
  }
}
Casino
Standard Casino pay-in pay-out Flow
Registration and getting deposits:

API - Integrate "POST Create new user account" into your registration process, so players will have dedicated balance upon registration.

UI - Ask a customer for desirable deposit amount, and preferred currency for payment.

API - Get the minimum payment amount for the selected currency pair (payment currency to your payout wallet currency) with the "GET Minimum payment amount" method;

API - Get the estimate of the total amount in crypto with "GET Estimated price" and check that it is larger than the minimum payment amount from step 4;

API - Call the "POST Deposit with payment" method to create a payment and get the deposit address (in our example, the generated BTC wallet address is returned from this method);

UI - Ask a customer to send the payment to the generated deposit address (in our example, user has to send BTC coins);

UI - A customer sends coins, NOWPayments processes and exchanges them (if required), and credit the payment to your players' balance;

API - You can get the payment status either via our IPN callbacks or manually, using "GET Payment Status" and display it to a customer so that they know when their payment has been processed;

API - you call the list of payments made to your account via the "GET List of payments" method;

Payouts:

UI - ask the player for desirable amount, coin and address for payout.

API - call the player balance with "GET user balance" method and check if player has enough balance.

API - call "POST validate address" to check if the provided address is valid on the blockchain.

API - call "POST write off your account" method to collect the requested amount from player's balance to your master balance.

API - call "POST Create payout" to create a payout.

API - create an OTP password for 2fa validation using external libraries.

API - call "POST Verify payout" to validate a payout with 2fa code.

API - You can get the payout status either via our IPN callbacks or manually, using "GET Payout Status" and display it to a customer so that they know when the transaction has been processed;

UI - NOWPayments processes payout and credits it to your players' wallet;

All related information about your operations will also be available in your NOWPayments dashboard.

If you have any additional questions about integration feel free to drop a message to partners@nowpayments.io for further guidance.

Auth and API status
This set of methods allows you to check API availability and get a JWT token which is requires as a header for some other methods.

GET
Get API status
https://api.nowpayments.io/v1/status
This is a method to get information about the current state of the API. If everything is OK, you will receive an "OK" message. Otherwise, you'll see some error.

Example Request
200
curl
curl --location 'https://api.nowpayments.io/v1/status'
200 OK
Example Response
Body
Headers (15)
json
{
  "message": "OK"
}
POST
Create new user account
https://api.nowpayments.io/v1/sub-partner/balance
This is a method to create an account for your user. After this you'll be able to generate a payment(/v1/sub-partner/payment) or deposit(/v1/sub-partner/deposit) for topping up its balance as well as withdraw funds from it.

You can integrate this endpoint into the registration process on your service so upon registration, players will already have dedicated NOWPayments balance as your sub-user.

Body:

Name : a unique user identifier; you can use any string which doesn’t exceed 30 characters (but NOT an email)

AUTHORIZATION
Bearer Token
Token
{{token}}

HEADERS
Authorization
Bearer *your_jwt_token*

Content-Type
application/json

PARAMS
Body
raw (json)
json
{
    "name": "test1"
}
Example Request
200
curl
curl --location 'https://api.nowpayments.io/v1/sub-partner/balance' \
--data '{
    "name": "test1"
}'
200 OK
Example Response
Body
Headers (0)
Text
{
  "result": {
    "id": "1515573197",
    "name": "test1",
    "created_at": "2022-10-09T21:56:33.754Z",
    "updated_at": "2022-10-09T21:56:33.754Z"
  }
}
GET
Get users
https://api.nowpayments.ioo/v1/sub-partner?id=111&offset=1&limit=10&order=DESC
This method returns the entire list of your users.

AUTHORIZATION
Bearer Token
Token
{{token}}

HEADERS
Authorization
Bearer *your_jwt_token*

PARAMS
id
111

int or array of int (optional)

offset
1

(optional) default 0

limit
10

(optional) default 10

order
DESC

ASC / DESC (optional) default ASC

Example Request
200
curl
curl --location 'https://api.nowpayments.ioo/v1/sub-partner?offset=0&limit=10&order=DESC'
Example Response
Body
Headers (0)
View More
Text
{
  "result": [
    {
      "id": "111394288",
      "name": "test",
      "created_at": "2022-10-06T16:42:47.352Z",
      "updated_at": "2022-10-06T16:42:47.352Z"
    },
    {
      "id": "1515573197",
      "name": "test1",
      "created_at": "2022-10-09T21:56:33.754Z",
      "updated_at": "2022-10-09T21:56:33.754Z"
    }
  ],
  "count": 2
}
POST
Deposit with payment
https://api.nowpayments.io/v1/sub-partner/payment
It will work as general white-labeled payment directly into user balance. You only need to show the user required for making a deposit information using the response of that endpoint.

This method allows you to top up a user account with a general payment.
You can check the actual payment status by using GET 9 Get payment status request.

AUTHORIZATION
Bearer Token
Token
{{token}}

HEADERS
x-api-key
{{x-api-key}}

Content-Type
application/json

Body
raw (json)
json
{
    "currency": "trx",
    "amount": 0.3,
    "sub_partner_id": "1631380403",
    "fixed_rate": false
}
Example Request
Deposit with payment
curl
curl --location 'https://api.nowpayments.io/v1/sub-partner/payment' \
--header 'x-api-key: {{x-api-token}}' \
--data '{
    "currency": "trx",
    "amount": 50,
    "sub_partner_id": "1631380403",
    "fixed_rate": false
}'
200 OK
Example Response
Body
Headers (0)
View More
Text
{
  "result": {
    "payment_id": "5250038861",
    "payment_status": "waiting",
    "pay_address": "TSszwFcbpkrZ2H85ZKsB6bEV5ffAv6kKai",
    "price_amount": 50,
    "price_currency": "trx",
    "pay_amount": 50,
    "amount_received": 0.0272467,
    "pay_currency": "trx",
    "order_id": null,
    "order_description": null,
    "ipn_callback_url": null,
    "created_at": "2022-10-11T10:49:27.414Z",
    "updated_at": "2022-10-11T10:49:27.414Z",
    "purchase_id": "5932573772",
    "smart_contract": null,
    "network": "trx",
    "network_precision": null,
    "time_limit": null,
    "burning_percent": null,
    "expiration_estimate_date": "2022-10-11T11:09:27.418Z",
    "valid_until": "valid_until_timestamp",
    "type": "crypto2crypto"
  }
}
GET
Get list of payments
https://api.nowpayments.io/v1/payment/?limit=10&page=0&sortBy=created_at&orderBy=asc&dateFrom=2020-01-01&dateTo=2021-01-01
Returns the entire list of all transactions created with certain API key.
The list of optional parameters:

limit - number of records in one page. (possible values: from 1 to 500);
page - the page number you want to get (possible values: from 0 to page count - 1);
invoiceId - filtering payments by certain invoice ID;
sortBy - sort the received list by a paramenter. Set to created_at by default (possible values: payment_id, payment_status, pay_address, price_amount, price_currency, pay_amount, actually_paid, pay_currency, order_id, order_description, purchase_id, outcome_amount, outcome_currency);
orderBy - display the list in ascending or descending order. Set to asc by default (possible values: asc, desc);
dateFrom - select the displayed period start date (date format: YYYY-MM-DD or yy-MM-ddTHH:mm:ss.SSSZ);
dateTo - select the displayed period end date (date format: YYYY-MM-DD or yy-MM-ddTHH:mm:ss.SSSZ);
AUTHORIZATION
Bearer Token
Token
{{token}}

HEADERS
x-api-key
{{your_api_key}}

Authorization
Bearer *your_jwt_token*

PARAMS
limit
10

page
0

sortBy
created_at

orderBy
asc

dateFrom
2020-01-01

dateTo
2021-01-01

Example Request
200
View More
curl
curl --location 'https://api.nowpayments.io/v1/payment/?limit=10&page=0&sortBy=created_at&orderBy=asc&dateFrom=2020-01-01&dateTo=2021-01-01' \
--header 'x-api-key: <your_api_key>' \
--header 'Authorization: <your_jwt_token>'
200 OK
Example Response
Body
Headers (20)
View More
json
{
  "data": [
    {
      "payment_id": 5524759814,
      "payment_status": "finished",
      "pay_address": "TNDFkiSmBQorNFacb3735q8MnT29sn8BLn",
      "price_amount": 5,
      "price_currency": "usd",
      "pay_amount": 165.652609,
      "actually_paid": 180,
      "pay_currency": "trx",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "4944856743",
      "outcome_amount": 178.9005,
      "outcome_currency": "trx"
    },
    {
      "payment_id": 5867063509,
      "payment_status": "expired",
      "pay_address": "TVKHbLc47BnMbdE7QN4X5Q1FtyZLGGiTo8",
      "price_amount": 5,
      "price_currency": "usd",
      "pay_amount": 165.652609,
      "actually_paid": 0,
      "pay_currency": "trx",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "5057851130",
      "outcome_amount": 164.6248468,
      "outcome_currency": "trx"
    },
    {
      "payment_id": 5745459419,
      "payment_status": "waiting",
      "pay_address": "3EZ2uTdVDAMFXTfc6uLDDKR6o8qKBZXVkj",
      "price_amount": 3999.5,
      "price_currency": "usd",
      "pay_amount": 0.17070286,
      "actually_paid": 0,
      "pay_currency": "btc",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "5837122679",
      "outcome_amount": 0.1687052,
      "outcome_currency": "btc"
    },
    {
      "payment_id": 4650948408,
      "payment_status": "waiting",
      "pay_address": "394UZCUdx3NN8VDsCZW8c6AzP7cXEXA8Xq",
      "price_amount": 3999.5,
      "price_currency": "usd",
      "pay_amount": 0.8102725,
      "actually_paid": 0,
      "pay_currency": "btc",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "5094859409",
      "outcome_amount": 0.8019402,
      "outcome_currency": "btc"
    },
    {
      "payment_id": 5605634688,
      "payment_status": "expired",
      "pay_address": "3EWJaZBaRWbPjSBTpgFcvxpnXLJzFDCHqW",
      "price_amount": 500,
      "price_currency": "usd",
      "pay_amount": 993.87178656,
      "actually_paid": 0,
      "pay_currency": "bcd",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "5817305007",
      "outcome_amount": 988.9016296,
      "outcome_currency": "bcd"
    },
    {
      "payment_id": 5241856814,
      "payment_status": "expired",
      "pay_address": "qzkshdh94vhdcyuejjf8ltcy2cl246hw0c68t36z69",
      "price_amount": 500,
      "price_currency": "usd",
      "pay_amount": 1.85459941,
      "actually_paid": 0,
      "pay_currency": "bch",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "5941190675",
      "outcome_amount": 1.8451261,
      "outcome_currency": "bch"
    },
    {
      "payment_id": 5751462089,
      "payment_status": "expired",
      "pay_address": "AYyecr8WKVpj2PNonjyUpn9sCHFyFMLdN1",
      "price_amount": 500,
      "price_currency": "usd",
      "pay_amount": 56.4344495,
      "actually_paid": 0,
      "pay_currency": "btg",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "6229667127",
      "outcome_amount": 56.151958,
      "outcome_currency": "btg"
    },
    {
      "payment_id": 6100223670,
      "payment_status": "expired",
      "pay_address": "0x6C3E920D0fdAF45c75b6c00f25Aa6a58429d4efB",
      "price_amount": 500,
      "price_currency": "usd",
      "pay_amount": 496.84604252,
      "actually_paid": 0,
      "pay_currency": "dai",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "5376931412",
      "outcome_amount": 489.9433465,
      "outcome_currency": "dai"
    },
    {
      "payment_id": 4460859238,
      "payment_status": "expired",
      "pay_address": "3C85TUuBKEkoZZsTawiJhYZtVVLgE4GWqj",
      "price_amount": 500,
      "price_currency": "usd",
      "pay_amount": 0.02596608,
      "actually_paid": 0,
      "pay_currency": "btc",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "5652098489",
      "outcome_amount": 0.025819,
      "outcome_currency": "btc"
    },
    {
      "payment_id": 4948632928,
      "payment_status": "expired",
      "pay_address": "DLmK6vLURgHoWVZrQztthSqV71CBePG5k5",
      "price_amount": 500,
      "price_currency": "usd",
      "pay_amount": 154569.92936569,
      "actually_paid": 0,
      "pay_currency": "doge",
      "order_id": "RGDBP-21314",
      "order_description": "Apple Macbook Pro 2019 x 1",
      "purchase_id": "4811984625",
      "outcome_amount": 153789.0997188,
      "outcome_currency": "doge"
    }
  ],
  "limit": 10,
  "page": 0,
  "pagesCount": 6,
  "total": 59
}
Payouts
This set of methods will allow you to set up fully automated payouts-on-demand for your players.

Recommended payouts requesting flow using API:

Check if your payout address is valid using POST Validate address endpoint;
If it's valid, create a withdrawal using POST Create payout endpoint;
Verify your payout with 2fa (by default it's mandatory) using POST Verify payout endpoint;
2FA automation:

Using the API you can automate 2fa by implementing the OTP generation library in your code and set it up in your dashboard. "Dashboard" - "Account settings" - "Two step authentification" - "Use an app"

Save the secret key and set it up in your favorite 2FA application as well, otherwise you won't be able to get access to your dashboard!

Please note:

Payouts can be requested only using a whitelisted IP address, and to whitelisted wallet addresses. It's a security measure enabled for each partner account by default.

You can whitelist both of these anytime dropping a formal request using your registration email to partners@nowpayments.io.

For more information about whitelisting you can reach us at partners@nowpayments.io.

GET
List of payouts
https://api.nowpayments.io/v1/payout
This endpoint allows you to get a list of your payouts.

The list of available parameters:

batch_id: batch ID of enlisted payouts;
status: the statuses of enlisted payouts;
order_by: can be id, batchId, dateCreated, dateRequested, dateUpdated, currency, status;
order: 'asc' or 'desc' order;
date_from: beginning date of the requested payouts;
date_to: ending date of the requested payouts;
limit: how much results to show;
page: the current page;
HEADERS
x-api-key
{{your_api_key}}

Example Request
List of payouts
curl
curl --location 'https://api.nowpayments.io/v1/payout'
200 OK
Example Response
Body
Headers (1)
View More
json
{
  "payouts": [
    {
      "id": "5000248325",
      "batch_withdrawal_id": "5000145498",
      "status": "FINISHED",
      "error": null,
      "currency": "trx",
      "amount": "94.088939",
      "address": "[payout address]",
      "extra_id": null,
      "hash": "[hash]",
      "ipn_callback_url": null,
      "payout_description": null,
      "is_request_payouts": true,
      "unique_external_id": null,
      "created_at": "2023-04-06T14:44:59.684Z",
      "requested_at": "2023-04-06T14:45:55.505Z",
      "updated_at": "2023-04-06T14:49:08.031Z"
    },
    {
      "id": "5000247307",
      "batch_withdrawal_id": "5000144539",
      "status": "FINISHED",
      "error": null,
      "currency": "trx",
      "amount": "10.000000",
      "address": "[payout address]",
      "extra_id": null,
      "hash": "[hash]",
      "ipn_callback_url": null,
      "payout_description": null,
      "is_request_payouts": true,
      "unique_external_id": null,
      "created_at": "2023-04-05T19:21:40.836Z",
      "requested_at": "2023-04-05T19:23:17.111Z",
      "updated_at": "2023-04-05T19:27:30.895Z"
    }
  ]
}
GET
Get available currencies
https://api.nowpayments.io/v1/currencies
This is a method for obtaining information about all cryptocurrencies available for payments for your current setup of payout wallets.
Optional parameters:

fixed_rate(optional) - boolean, can be true or false. Returns avaliable currencies with minimum and maximum amount of the exchange.
HEADERS
x-api-key
{{your_api_key}}

Example Request
200
curl
curl --location 'https://api.nowpayments.io/v1/currencies' \
--header 'x-api-key: <your_api_key>'
200 OK
Example Response
Body
Headers (20)
View More
json
{
  "currencies": [
    "btg",
    "eth",
    "xmr",
    "zec",
    "xvg",
    "ada",
    "ltc",
    "bch",
    "qtum",
    "dash",
    "xlm",
    "xrp",
    "xem",
    "dgb",
    "lsk",
    "doge",
    "trx",
    "kmd",
    "rep",
    "bat",
    "ark",
    "waves",
    "bnb",
    "xzc",
    "nano",
    "tusd",
    "vet",
    "zen",
    "grs",
    "fun",
    "neo",
    "gas",
    "pax",
    "usdc",
    "ont",
    "xtz",
    "link",
    "rvn",
    "bnbmainnet",
    "zil",
    "bcd",
    "usdt",
    "usdterc20",
    "cro",
    "dai",
    "ht",
    "wabi",
    "busd",
    "algo",
    "usdttrc20",
    "gt",
    "stpt",
    "ava",
    "sxp",
    "uni",
    "okb",
    "btc"
  ]
}
Custody
This section describes our custody feature.

If you prefer, you can set up a full-fledged billing solution. Our API allows you to create user accounts for your players with dedicated balance management for each one of them, transfers between these balances, direct deposits and much more in future.

In order to do that you need:

Create a user balance with "Create new user account" method. You can integrate this endpoint into the registration process on your service so upon registration, players will already have dedicated NOWPayments balance as your sub-user.
To show the balance at the frontend you can get it with "GET user balance" method. It will return you an array of user balances you can list in the back office.
To set up top ups, you can use "POST deposit with payment"; it will work as general white-labeled payment directly into user balance. You only need to show the user required for making a deposit information using the response of that endpoint. It's also possible to automatically credit it to player taking advantage of IPN system.
Managing debit and credit you are meant to use "POST deposit from master account" and "POST write-off" endpoints to make transactions from master balance to user balances, and vice-versa, enlisting all of these operations is possible using "GET transfer" and "GET all transfers" endpoints.
For payouts administration you will need to collect funds from your players' balance and withdraw it using payouts API.
POST
Deposit from your master account
https://api.nowpayments.io/v1/sub-partner/deposit
This is a method for transferring funds from your master account to a user's one.
The actual information about the transfer's status can be obtained via Get transfer method.

The list of available statuses:

CREATED - the transfer is being created;
WAITING - the transfer is waiting for payment;
FINISHED - the transfer is completed;
REJECTED - for some reason, transaction failed;
AUTHORIZATION
Bearer Token
Token
{{token}}

HEADERS
x-api-key
{{x-api-token}}

Content-Type
application/json

Body
raw (json)
json
{
    "currency": "trx",
    "amount": 0.3,
    "sub_partner_id": "1631380403"
}
Example Request
200
curl
curl --location 'https://api.nowpayments.io/v1/sub-partner/deposit' \
--header 'x-api-key: {{x-api-token}}' \
--data '{
    "currency": "usddtrc20",
    "amount": 0.7,
    "sub_partner_id": "111394288"
}'
Example Response
Body
Headers (0)
View More
Text
{
    "result": {
        "id": "19649354",
        "from_sub_id": "5209391548", //main account
        "to_sub_id": "111394288", //sub account
        "status": "WAITING",
        "created_at": "2022-10-11T10:01:33.323Z",
        "updated_at": "2022-10-11T10:01:33.323Z",
        "amount": "0.7",
        "currency": "usddtrc20"
    }
}
POST
Create plan
https://api.nowpayments.io/v1/subscriptions/plans
This is the method to create a Recurring Payments plan. Every plan has its unique ID which is required for generating separate payments.

Available parameters:
"title": the name of your recurring payments plan;
"interval_day": recurring payments duration in days;
"amount" : amount of funds paid in fiat/crypto;
"currency" : crypto or fiat currency we support;
"ipn_callback_url" : your IPN_callback url;
"success_url" : url user got redirected in case payment was successful;
"cancel_url" : url user got redirected in case payment was cancelled;
"partially_paid_url" : url user got redirected in case payment was paid not in full amount;

AUTHORIZATION
Bearer Token
Token
{{token}}

HEADERS
x-api-key
{{your_api_key}}

Content-Type
application/json

Body
raw (json)
json
{
    "title": "second sub plan",
    "interval_day": 3,
    "amount": 1,
    "currency" : "usd"
}
Example Request
200
curl
curl --location 'https://api.nowpayments.io/v1/subscriptions/plans' \
--header 'x-api-key: <your_api_key>' \
--data '{
    "title": "second sub plan",
    "interval_day": 1,
    "amount": 0.5,
    "currency" : "usd"
}'
200 OK
Example Response
Body
Headers (0)
View More
Text
{
  "result": {
    "id": "1062307590",
    "title": "second sub plan",
    "interval_day": "1",
    "ipn_callback_url": null,
    "success_url": null,
    "cancel_url": null,
    "partially_paid_url": null,
    "amount": 0.5,
    "currency": "USD",
    "created_at": "2022-10-04T16:28:55.423Z",
    "updated_at": "2022-10-04T16:28:55.423Z"
  }
}
POST
Create an email subscription
https://api.nowpayments.io/v1/subscriptions
This method allows you to send payment links to your customers via email. A day before the paid period ends, the customer receives a new letter with a new payment link.

subscription_plan_id - the ID of the payment plan your customer chooses; such params as the duration and amount will be defined by this ID;
email - your customer’s email to which the payment links will be sent;

AUTHORIZATION
Bearer Token
Token
{{token}}

HEADERS
x-api-key
{{your_api_key}}

Content-Type
application/json

Body
raw (json)
json
{
    "subscription_plan_id": 76215585,
    "email": "test@example.com"
}
Example Request
200
curl
curl --location 'https://api.nowpayments.io/v1/subscriptions' \
--header 'x-api-key: <enter_your_api_key>' \
--data-raw '{
    "subscription_plan_id": 76215585,
    "email": "test@example.com"
}'
200 OK
Example Response
Body
Headers (0)
View More
Text
{
  "result": {
    "id": "148427051",
    "subscription_plan_id": "76215585",
    "is_active": false,
    "status": "WAITING_PAY",
    "expire_date": "2022-10-10T13:46:18.476Z",
    "subscriber": {
      "email": "test@example.com"
    },
    "created_at": "2022-10-10T13:46:18.476Z",
    "updated_at": "2022-10-10T13:46:18.476Z"
  }
}
Conversions
Conversions API allows you to exchange coins within your custody user account.

Mass payouts
This set of methods will allow you to make payouts from your custody to unlimited number of wallets. Fast and secure.

Recommended payouts requesting flow using API:

Check if your payout address is valid using POST Validate address endpoint;
If it's valid, create a withdrawal using POST Create payout endpoint;
Verify your payout with 2fa (by default it's mandatory) using POST Verify payout endpoint;
2FA automation:

Using the API you can automate 2fa by implementing the OTP generation library in your code and set it up in your dashboard. "Dashboard" - "Account settings" - "Two step authentification" - "Use an app"

Save the secret key and set it up in your favorite 2FA application as well, otherwise you won't be able to get access to your dashboard!

Please note:

Payouts can be requested only using a whitelisted IP address, and to whitelisted wallet addresses. It's a security measure enabled for each partner account by default.

You can whitelist both of these anytime dropping a formal request using your registration email to partners@nowpayments.io.

For more information about whitelisting you can reach us at partners@nowpayments.io.

POST
Verify payout
https://api.nowpayments.io/v1/payout/:batch-withdrawal-id/verify
This method is required to verify payouts by using your 2FA code.
You’ll have 10 attempts to verify the payout. If it is not verified after 10 attempts, the payout will remain in ‘creating’ status.
Payout will be processed only when it is verified.

If you have 2FA app enabled in your dashboard, payouts will accept 2FA code from your app. Otherwise the code for payouts validation will be sent to your registration email.

Please take a note that unverified payouts will be automatically rejected in an hour after creation.

Next is a description of the required request fields:

:batch-withdrawal-id - payout id you received in 2. Create payout method;
verification_code - 2fa code you received with your Google Auth app or via email;
In order to establish an automatic verification of payouts, you should switch 2FA through the application.
There are several libraries for different frameworks aimed on generating a 2FA codes based on a secret key from your account settings, for example, Speakeasy for JavaScript.
We do not recommend to change any default settings.

Plain Text
const 2faVerificationCode = speakeasy.totp({
      your_2fa_secret_key,
      encoding: 'base32',
})
AUTHORIZATION
Bearer Token
Token
{{token}}

HEADERS
x-api-key
{{your_api_key}}

Authorization
Bearer *your_jwt_token*

PATH VARIABLES
batch-withdrawal-id
Body
raw (json)
json
{
  "verification_code": "123456"
}
Example Request
200
curl
curl --location 'https://api.nowpayments.io/v1/payout/5000000191/verify' \
--header 'x-api-key: {{your_api_key}}' \
--header 'Authorization: Bearer *your_jwt_token*' \
--header 'Content-Type: application/json' \
--data '{
  "verification_code": "123456"
}'
200 OK
Example Response
Body
Headers (0)
OK
GET
Get payout status
https://api.nowpayments.io/v1/payout/<payout_id>
Get the actual information about the payout. You need to provide the ID of the payout in the request.

NOTE! You should make the get payout status request with the same API key that you used in the creat_payout request.

Here is the list of available statuses:

creating;
processing;
sending;
finished;
failed;
rejected;
HEADERS
x-api-key
{{your_api_key}}

Example Request
200
curl
curl --location 'https://api.nowpayments.io/v1/payout/:payout_id' \
--header 'x-api-key: <your_api_key>' \
--header 'Authorization: Bearer *your_jwt_token*'
200 OK
Example Response
Body
Headers (0)
View More
json
[
  {
    "id": "<payout_id>",
    "address": "<payout_address>",
    "currency": "trx",
    "amount": "200",
    "batch_withdrawal_id": "<batchWithdrawalId>",
    "status": "WAITING",
    "extra_id": null,
    "hash": null,
    "error": null,
    "is_request_payouts": false,
    "ipn_callback_url": null,
    "unique_external_id": null,
    "payout_description": null,
    "created_at": "2020-11-12T17:06:12.791Z",
    "requested_at": null,
    "updated_at": null
  }
]
GET
List of payouts
https://api.nowpayments.io/v1/payout
This endpoint allows you to get a list of your payouts.

The list of available parameters:

batch_id: batch ID of enlisted payouts;
status: the statuses of enlisted payouts;
order_by: can be id, batchId, dateCreated, dateRequested, dateUpdated, currency, status;
order: 'asc' or 'desc' order;
date_from: beginning date of the requested payouts;
date_to: ending date of the requested payouts;
limit: how much results to show;
page: the current page;
HEADERS
x-api-key
{{your_api_key}}