from flask import Flask, redirect, render_template, request, session, url_for
import torch
torch.multiprocessing.freeze_support()
from farm.infer import Inferencer
import gc

model_dir_cog = "cognitiveempathy"
model_dir_emo = "emotionalempathy"

app = Flask(__name__)

def inference_cognitive(inferencer, basic_texts):
    result = inferencer.inference_from_dicts(dicts=basic_texts)
    label = result[0]['predictions'][0]['label']
    return label.split(',')[0]

def inference_emotional(inferencer, basic_texts):
    result = inferencer.inference_from_dicts(dicts=basic_texts)
    label = result[0]['predictions'][0]['label']
    return label.split(',')[0]

def calculate_empathy_score(emo_labels, cog_labels):
    score = 0
    for label in emo_labels.values():
        if 'empathic' in label and 'non' not in label:
            score += 3
        elif 'non-empathic' in label:
            score += 1
        elif 'neutral' in label:
            score += 2
        else:
            score += 0

    for label in cog_labels.values():
        if 'empathic' in label and 'non' not in label:
            score += 3
        elif 'non-empathic' in label:
            score += 1
        elif 'neutral' in label:
            score += 2
        else:
            score +=0

    # print(score)
    percentage_score = (score / 18) * 100
    return int(percentage_score)

def get_feedback(score):
    feedback = ''
    if score > 0 and score <= 20:
        feedback = '''Very weak: Your feedback still lacks a lot of empathy. Try to include more emotional and cognitive aspects in your review of the peer's business idea.'''
    elif score > 20 and score <= 40:
        feedback = '''Weak: Your feedback is still missing a lot of empathic aspects. Try to add more emotional feelings and step further into your peer's perspective.'''
    elif score > 40 and score <= 60:
        feedback = '''Neutral. Your feedback is written very objectively. Try to include more of your personal thoughts and add further explanations, elaborations and personal feelings to your review.'''
    elif score > 60 and score <= 80:
        feedback = '''Good. Your feedback shows a good level of empathy. You managed to include personal feelings and step into the peer's perspective to elaborate fully on the business idea. Try to add a few further elaborations and personal feelings to your review.'''
    elif score > 80 and score <= 100:
        feedback = "Very well. Your feedback is very empathic!"

    return feedback

def get_cognitive_feedback():
    cognitive_feedback_texts = {
        'strength': {
            'empathic': "Well done, you managed to step outside your own perspective and think from the peer’s perspective. Moreover, you review includes details, explanations, questions, or direct addressing of the author to better understand and elaborate on the peer’s perspective.",
            'non-empathic':"Your feedback is very short and does not include the peer’s perspective. Try to step into his shoes and add examples, explanations or further elaborations to your feedback. ",
            'neutral':"Try to add more contextual rather than formal aspects of the peer’s business idea and add further explanations and elaborations on your thoughts by thinking from the peer’s perspective. "
        },
        'weakness':{
            'empathic': "Well done, you managed tostep outside your own perspective and think from the peer’s perspective. Moreover, you review includes details, explanations, questions, or direct addressing of the author to better understand and elaborate on the peer’s perspective.",
            'non-empathic':"Your feedback is very short and does not include the peer’s perspective. Try to step into his shoes and add examples, explanations or further elaborations to your feedback. Explain, why the mentioned weakness is important to consider.",
            'neutral':"Try to add more contextual rather than formal aspects of the peer’s business idea and add further explanations and elaborations on your thoughts by thinking from the peer’s perspective. Explain, why the mentioned weakness is important to consider. "
        },
        'suggestion':{
            'empathic': "Well done, you managed to step outside your own perspective and thinks from the peer’s perspective. Moreover, you review includes details, explanations, questions, or direct addressing of the author to better understand and elaborate on the peer’s perspective.",
            'non-empathic':"Your feedback is very short and does not include the peer’s perspective. Try to step into his shoes and add examples, explanations or further elaborations to your feedback. Be very specific on your instructions for improvements and explain them in detail.",
            'neutral':"Try to add more contextual rather than formal aspects of the peer’s business idea and add further explanations and elaborations on your thoughts by thinking from the peer’s perspective. Be very specific on your instructions for improvements and explain them in detail. "
        }
    }

    return cognitive_feedback_texts



def get_emotional_feedback():
    emotional_feedback_texts = {
        'strength': {
            'empathic': "Well done, you managed to show your own personal feelings and emotions towards the peer’s business idea",
            'non-empathic':"Try to respond in an emotional manner to your peer’s business idea by including your personal feelings and emotions. Share your excitement for the strengths you have detected",
            'neutral':"You already used emotions in your feedback text, but you are still missing to state your own personal feelings by using personal pronouns when describing the strengths. "
        },
        'weakness':{
            'empathic': "Well done, you managed to show your own personal feelings and emotions towards the peer’s business idea.",
            'non-empathic':"Try to respond in an emotional manner to your peer’s business idea by including your personal feelings and emotions. Share your personal concerns or doubts for the weaknesses you have detected. ",
            'neutral':"You already used emotions in your feedback text, but you are still missing to state your own personal feelings by using personal pronouns when describing the weakness. "
        },
        'suggestion':{
            'empathic': "Well done, you managed to show your own personal feelings and emotions towards the peer’s business idea. ",
            'non-empathic':"Try to respond in an emotional manner to your peer’s business idea by including your personal feelings and emotions. ",
            'neutral':"You already used emotions in your feedback text, but you are still missing to state your own personal feelings by using personal pronouns when describing your suggestions for improvement. "
        }
    }

    return emotional_feedback_texts



@app.route('/', methods=['GET', 'POST'])
def index():
    inp1 = {}
    inp2 = {}
    inp3 = {}

    if request.method == 'POST':
        cog_labels = {}
        emo_labels = {}

        cognitive_inferencer= Inferencer.load(model_dir_cog)
        emotional_inferencer= Inferencer.load(model_dir_emo)

        inp1['text'] = request.form['strengths']
        inp2['text'] = request.form['weaknesses']
        inp3['text'] = request.form['suggestions']

        cog_labels['strength'] = inference_cognitive(cognitive_inferencer, [inp1])
        emo_labels['strength'] = inference_emotional(emotional_inferencer, [inp1])

        cog_labels['weakness'] = inference_cognitive(cognitive_inferencer, [inp2])
        emo_labels['weakness'] = inference_emotional(emotional_inferencer, [inp2])

        cog_labels['suggestion'] = inference_cognitive(cognitive_inferencer, [inp3])
        emo_labels['suggestion'] = inference_emotional(emotional_inferencer, [inp3])

        percentage_score = calculate_empathy_score(emo_labels, cog_labels)

        feedback = get_feedback(percentage_score)

        del cognitive_inferencer
        del emotional_inferencer

        # return redirect(url_for('index', perc_score=percentage_score, feedback=feedback, emo_labels=emo_labels, cog_labels=cog_labels))
        return render_template('index.html',
                                perc_score=percentage_score,
                                feedback=feedback,
                                emo_labels=emo_labels,
                                cog_labels=cog_labels,
                                emo_feedback=get_emotional_feedback(),
                                cog_feedback=get_cognitive_feedback(),)
    return render_template('index.html', onclick = "popup.html")

@app.route('/popup')
def popup():
    return render_template('popup.html')


if __name__ == '__main__':
    app.secret_key = 'you shall not guess'
    #app.run(threaded=True)
    app.run(host='0.0.0.0', port=5000, threaded=True)
