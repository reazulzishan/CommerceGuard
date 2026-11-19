# CommerceGuard · Episode 2 — "One parcel, two phones"

Narrator: VCTK p270 (English). Chat bubbles in Bangla with an English line under each.
Every model number is from notebooks/02_commerceguard_multimodel.ipynb. Market facts cite news sources (see POST_TEXTS).

[E01] PART 1
This is Dhaka. Every day, thousands of small online shops send parcels across this city. This one belongs to Rafi.

[E02] PART 1
Nadia likes a dress on his page. She sends one message, the most common message in Bangladeshi e-commerce.

[E03] PART 1
Cash on delivery, right? Rafi says yes. He packs the dress, pays the courier, and the parcel leaves his shop.

[E04] PART 1
Three days later, it still hasn't arrived. Nadia writes again, and this time, the tone has changed.

[E05] PART 1
When the parcel finally reaches her door, she opens it in front of the rider. It does not look like the photo. She refuses it.

[E06] PART 1
The parcel goes back to Rafi. He gets no money, he loses the delivery charge both ways, and the dress comes back used.

[E07] PART 1
This is not one unlucky seller. Courier companies themselves say a typical shop delivers only seventy five to eighty five percent of its parcels.

[E08] PART 1
So why does almost everyone in Bangladesh pay cash at the door? To understand that, we have to go back to 2021.

[E09] PART 1
Platforms like Evaly and e-Orange took money in advance with huge discounts. Then the deliveries stopped.

[E10] PART 1
Officials put the money stuck in just three of these companies at around three thousand crore taka. By September 2022, only about two hundred fifty crore had gone back, to around twenty nine thousand customers.

[E11] PART 1
After that, people stopped trusting advance payment. Cash on delivery became the shield. But a shield for the buyer moves the risk to the seller.

[E12] PART 2
So this is the question for CommerceGuard. Can machine learning warn Rafi before the parcel leaves, not after it comes back?

[E13] PART 2
I built three models. The first one listens to the customer. The second one looks at the order. The third, from episode one, watches the delivery.

[E14] PART 2
For the customer's voice, I used a public dataset of real reviews from Daraz and Pickaboo. Seventy eight thousand reviews, in Bangla and English.

[E15] PART 2
First trap: almost fourteen thousand reviews were exact copies. After removing them, sixty four thousand were left, and sixteen percent were unhappy.

[E16] PART 2
And what do unhappy customers talk about? They mention returns and refunds fifteen times more often than happy ones, and damaged products twelve times more.

[E17] PART 2
Second trap: reviews of the same product share words. So I split by product. No product appears in both training and test.

[E18] PART 2
The model reads only the text, never the star rating, because a chat message has no stars. Characters and words together, with logistic regression.

[E19] PART 2
On reviews from products it had never seen, it scored zero point eight two on precision recall. Random guessing scores zero point one seven. And on Bangla reviews, it did even better: zero point eight six.

[E20] PART 2
Now the order itself. There is no public dataset that shows what happened to Bangladeshi orders. So I used the closest real dataset: more than half a million order items from a cash on delivery market in Pakistan, from 2016 to 2018.

[E21] PART 2
And here is the surprise. Cash on delivery orders were cancelled far less: eight percent, against fifty eight percent for online payments, many of which are simply abandoned payments.

[E22] PART 2
But cash on delivery orders were refunded five times more often. Twenty percent, against four percent. Exactly Rafi's problem.

[E23] PART 3
For this model, history matters, but only from the past. A customer's cancellations count only from earlier days, and refunds only from orders placed at least thirty days before.

[E24] PART 3
Split by time again, and the test set used once. The cancellation model scored zero point seven nine, against zero point four six for random. Refunds are harder: zero point three five, against zero point one seven.

[E25] PART 3
Then the engine. It turns the risks into one number per order, the expected loss, and ranks the whole day. Reviewing just the top ten percent of order items catches fifty one percent of the loss.

[E26] PART 3
Now let's go back to Nadia and Rafi, and let CommerceGuard read the same chat.

[E27] PART 3
Her first message: twenty percent. Three days, still waiting: ninety. It looks fake: ninety five. I want a refund: ninety four.

[E28] PART 3
And a happy customer, writing Bangla in Roman letters: zero percent. The model was never trained on these exact messages. It learned from real reviews.

[E29] PART 3
With this, Rafi could call Nadia before shipping, ask for a small advance, or send a clearer photo. Small steps, decided by risk, not by guesswork.

[E30] PART 3
The honest limits: reviews are a proxy for complaints, the order data is from Pakistan, not Bangladesh, and the costs are examples. With real data from Bangladeshi sellers, this gets much stronger.

[E31] PART 3
That is CommerceGuard, version two. One step at a time. One model at a time. Predict risk. Understand behavior. Reduce preventable losses.

# Reel outro hooks (2 parts)
[F1] Next part: does it work on products it has never seen? And the order model that found Rafi's problem.
[F2] The full episode is on YouTube. Search CS Funda official.
