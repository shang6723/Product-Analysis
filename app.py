from flask import Flask, render_template, json, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from pprint import pprint
import pymongo
import requests
app = Flask(__name__)

# connect db
client = pymongo.MongoClient("""[your mongoDB info]""")
db = client.test

@app.route("/")
def main():
	first_message = db.first_message.find_one()
	second_posmessage = db.second_posmessage.find_one()
	second_negmessage = db.second_negmessage.find_one()
	return render_template('index.html', first_msg=first_message[u'message']
	, second_posmsg=second_posmessage[u'message'], second_negmsg=second_negmessage[u'message'])

@app.route("/sendsms",methods=['POST'])
def sendsms():
	_name = request.form['inputName']
	_phone = request.form['inputPhone']
	_product = request.form['inputProduct']

	account_sid = """[your sid]"""
	auth_token = """[your token]"""

	first_message = db.first_message.find_one()
	message = first_message[u'message'].replace('<name>', _name)
	message = message.replace('<productType>', _product)

	# send sms
	client = Client(account_sid, auth_token)
	client.api.account.messages.create(
			to = "+1"+_phone,
			from_ = """[your company phone number]""",
			body = message)


	# record customer info
	# customer_info = {
	# 	'name':_name,
	# 	'phone':'+1'+_phone,
	# 	'product':_product
	# }
	# customer_info_id = db.customer_infos.insert_one(customer_info).inserted_id
	# pprint(customer_info_id)

	"""Check data"""
	# for s in db.first_message.find():
	# 	pprint(s)

	"""Inital data"""
	# first_message = {
	# 	'message':'Hi <name>, I saw that your <productType> was delivered. How are you enjoying it so far?'
	# }
	# second_posmessage = {
	# 	'message':'Great, can you describe what you love most about the <productType>?',
	# }
	# second_negmessage = {
	# 	'message':'I am sorry to hear that, what do you dislike about <productType>?'
	# }
	# db.first_message.insert_one(first_message)
	# db.second_posmessage.insert_one(second_posmessage)
	# db.second_negmessage.insert_one(second_negmessage)

	return "SUCCESS SEND SMS "+_name+" "+_phone+" "+_product

@app.route("/analyzesms")
def analysis():
	"""Text Analysis preparation"""
	text_analytics_base_url = "https://westcentralus.api.cognitive.microsoft.com/text/analytics/v2.0/"
	sentiment_api_url = text_analytics_base_url + "sentiment"
	subscription_key = """[your key]"""
	assert subscription_key

	"""Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
	body = request.values.get('Body', None)
	cus_phone = request.values.get('From', 'None')


	documents = {'documents' : [
      {'id': '1', 'language': 'en', 'text': body}
    ]}

	# analyze message
	headers   = {"Ocp-Apim-Subscription-Key": subscription_key}
	response  = requests.post(sentiment_api_url, headers=headers, json=documents)
	sentiments = response.json()

	cus_info = db.customer_infos.find_one({'phone': cus_phone})
	second_posmessage = db.second_posmessage.find_one()
	second_negmessage = db.second_negmessage.find_one()

	if cus_info == None:
		cus_name = ''
		cus_product = 'product'
	else:
		cus_name = cus_info['name']
		cus_product = cus_info['product']

	# Start our TwiML response
	resp = MessagingResponse()

	if sentiments[u'documents'][0][u'score'] > 0.5:
		final_reply = second_posmessage[u'message'].replace('<name>', cus_name)
		final_reply = final_reply.replace('<productType>', cus_product)
	else:
		final_reply = second_negmessage[u'message'].replace('<name>', cus_name)
		final_reply = final_reply.replace('<productType>', cus_product)
	resp.message(final_reply)
	# pprint (sentiments[u'documents'][0][u'score'])

	return str(resp)

@app.route("/edit_firstmsg",methods=['POST'])
def edit_firstmsg():
	newmsg = request.form['inputMessage']
	message = db.first_message.find_one()
	db.first_message.update_one(message, {"$set": { "message": newmsg }})
	return "SUCCESS EDIT FIRST MESSAGE"
@app.route("/edit_secondposmsg",methods=['POST'])
def edit_secondposmsg():
	newmsg = request.form['inputMessage']
	message = db.second_posmessage.find_one()
	db.second_posmessage.update_one(message, {"$set": { "message": newmsg }})
	return "SUCCESS EDIT SECOND POSITIVE MESSAGE"
@app.route("/edit_secondnegmsg",methods=['POST'])
def edit_secondnegmsg():
	newmsg = request.form['inputMessage']
	message = db.second_negmessage.find_one()
	db.second_negmessage.update_one(message, {"$set": { "message": newmsg }})
	return "SUCCESS EDIT SECOND NEGATIVE MESSAGE"

if __name__ == "__main__":
	app.run(debug=True)
