# CommerceGuard · Episode 1 — voiceover script (English, p270 voice)

Each block is one scene. `[S##]` = scene id used in the edit. `REEL n` = which FB/Insta part it belongs to.
Every number below comes from the notebook run (notebooks/01_commerceguard_delivery_risk.ipynb).

[S01] REEL 1
What if an online store could see a loss coming, before it actually happens?

[S02] REEL 1
Think about this. Every day, thousands of orders are placed online. But not every order ends well. Some customers reject the parcel at the door. Some orders get cancelled again and again. Some returns and refunds quietly eat the profit.

[S03] REEL 1
And most businesses only find out after the damage is done. So I asked a simple question. What if we could see the warning signs earlier?

[S04] REEL 1
That is the idea behind CommerceGuard. A risk system for e-commerce, built from scratch with machine learning. No ready-made AI. No large language models. Just real data, careful features, honest testing, and models that can explain themselves.

[S05] REEL 1
The long plan is big. Delivery failure, suspicious orders, refund abuse, customer behavior. But I am starting with one question you can actually test. When a customer clicks buy, can we tell if the delivery promise will be broken?

[S06] REEL 2
For this, I am using the Olist dataset. About one hundred thousand real orders from a Brazilian marketplace, split across nine tables. Orders, items, payments, customers, sellers, products, reviews and locations.

[S07] REEL 2
Before writing any model, I wrote down the rules. One row is one order. The prediction happens at checkout. So the model may only use what is known at checkout. And the final test set gets used once. Only once.

[S08] REEL 2
The first surprise came early. Every order has a new customer ID. When I matched people properly, only three point one percent of customers ever ordered twice. So the idea of judging a customer by their history? On this data, it barely exists.

[S09] REEL 2
Next, cleaning. Orders from 2016 were too few, and the last months were not fully delivered yet. So I kept January 2017 to July 2018. That left eighty nine thousand, eight hundred and fifty two delivered orders. And the last month, July 2018, I locked away completely, for later.

[S10] REEL 2
Then the target. An order is late if it arrives after the date the customer was promised. Six point eight percent of orders were late. But look at this. The median promise was twenty four days. The median actual delivery was eleven. Most parcels arrived thirteen days early, and still, seven in every hundred were late.

[S11] REEL 2
So the promise is padded, and it still fails. That told me the real problem is not speed. It is knowing which orders will go wrong.

[S12] REEL 3
Some places are much worse than others. Customers in Maranhão saw eighteen percent of orders arrive late. In Ceará, fourteen percent.

[S13] REEL 3
Now the features. Order time, number of items, price, freight, weight, payment type, the customer's state, the seller's state, and the distance between them, calculated from their postal codes.

[S14] REEL 3
One feature needed real care: the seller's past late rate. It is easy to cheat here by accident. So for every order, I only counted deliveries that had already finished before that order was placed. Nothing from the future.

[S15] REEL 3
Then a leakage check in code. Actual delivery date, carrier date, review score, final status. All of these happen after checkout, so none of them are allowed in. The notebook stops if one sneaks in.

[S16] REEL 3
And the split goes by time, not at random. The oldest seventy percent to train, the next fifteen to validate, and the newest fifteen to test. Because in real life, you always predict the future from the past.

[S17] REEL 4
First, the baseline. A model that just guesses at random gets a precision recall score of zero point zero nine seven on validation. Logistic regression reached zero point two two. Then LightGBM reached zero point three. Its top ten percent most risky orders caught thirty five percent of all the late ones.

[S18] REEL 4
I calibrated the scores on the validation set, so a thirty percent risk should mean roughly thirty percent. Then I opened the test set. Once.

[S19] REEL 4
And the score dropped. On the test months, LightGBM scored zero point one zero. Random would be zero point zero four. So it still finds late orders about two and a half times better than guessing. But not the number I hoped for.

[S20] REEL 5
Turning scores into review bands helped. Orders marked low risk were late three point three percent of the time. Moderate, eleven percent. High, twenty percent. That is a list a support team could actually work through.

[S21] REEL 5
I also asked the model to explain itself, using SHAP. The biggest factors were the month of the order, the customer's state, how many days were promised, and the seller's past late rate.

[S22] REEL 5
That first factor bothered me. The calendar month. It means the model partly memorised which months were bad last year. Keep that in mind.

[S23] REEL 6
Then my favourite experiment. Instead of only flagging risk, can we promise a better date? I trained a model to predict delivery time at a chosen confidence level, and picked that level on validation.

[S24] REEL 6
On the test months it promised orders nine point three days sooner. Sounds great. But ten point nine percent of them arrived late, against four percent for Olist. My first experiment failed.

[S25] REEL 6
So I went looking for why. Here is the weekly late rate. Late deliveries jumped to around twenty six percent in February and March 2018, right where my validation set sits. Then it calmed down in the test months. The world changed, and my model had no way to know.

[S26] REEL 7
The fix had to be something you can know at checkout. So I added one more signal: how late deliveries have been in the last thirty days, overall and to the customer's state. Only deliveries already finished count.

[S27] REEL 7
To judge it fairly, I finally unlocked July 2018. Six thousand one hundred and fifty six orders that no model and no decision had ever touched.

[S28] REEL 7
The risk model still found late orders about twice as well as random. The new promise was three point three days shorter than Olist's, twenty point three down to seventeen. But late deliveries went up from three point four to five point eight percent.

[S29] REEL 7
So, not a magic win. A real trade off. Promise faster, and accept a few more late parcels. Or keep the safe promise. Now that choice can be made with numbers, not guesses.

[S30] REEL 7
This is episode one. The data is from Brazil, and late is not the same as a failed delivery. Next, I want to work on cash on delivery failures, with real data from Bangladeshi sellers.

[S31] REEL 7
I will share the full notebook in the next episode, once CommerceGuard becomes a multi-model system. One step at a time. One model at a time. CommerceGuard. Predict risk. Understand behavior. Reduce preventable losses.

# Reel outro hooks (FB/Insta only, 3 parts)
[R1] Next part: the real problem, and how I stopped my own model from cheating.
[R2] Next part: what the model thinks makes an order late, and the experiment that failed.
[R3] The full episode is on YouTube. Search CS Funda official.
# Code walkthroughs (typed real code on screen)
[C01] Here is the code. One dictionary comprehension loads all eight CSV files, so I can check rows, missing values and duplicates for every table at once.
[C02] The fix is one merge. Join orders to customers, group by the unique customer ID, and count how many orders each real person made.
[C03] The label is a single comparison. If the delivery day is later than the promised date, the order is late. Then I print the rate.
[C04] In code, the key is merge as-of, with exact matches turned off. Each order can only see deliveries that finished strictly before it was placed.
[C06] Because the rows are sorted by purchase time, the split is just two slices. No shuffling, so the future can never leak into training.
[C07] LightGBM gets up to two thousand trees, but early stopping watches the validation score and keeps the best round. Here, that was round seventy eight.
[C08] The promise model is LightGBM again, with a quantile objective. Alpha sets how cautious the promise is. I tried six levels, and let validation choose.
[C09] Two binary searches find every delivery that finished in the thirty days before each order. With fewer than twenty, the value stays empty.
