from flask import Flask, redirect, url_for, render_template, request, flash
from gateway import generate_client_token, transact, find_transaction
from app import app
import os
import braintree

PORT = int(os.environ.get('PORT', 4567))

TRANSACTION_SUCCESS_STATUSES = [
    braintree.Transaction.Status.Authorized,
    braintree.Transaction.Status.Authorizing,
    braintree.Transaction.Status.Settled,
    braintree.Transaction.Status.SettlementConfirmed,
    braintree.Transaction.Status.SettlementPending,
    braintree.Transaction.Status.Settling,
    braintree.Transaction.Status.SubmittedForSettlement
]

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/checkouts/new', methods=['GET'])
def new_checkout():
    client_token = generate_client_token()
    return render_template('checkouts/new.html', client_token=client_token)

@app.route('/checkouts', methods=['POST'])
def create_checkout():
    result = transact({
        'amount': request.form['amount'],
        'payment_method_nonce': request.form['payment_method_nonce'],
        'options': {
            "submit_for_settlement": True
        }
    })

    if result.is_success or result.transaction:
        return redirect(url_for('show_checkout',transaction_id=result.transaction.id))
    else:
        for x in result.errors.deep_errors: flash('Error: %s: %s' % (x.code, x.message))
        return redirect(url_for('new_checkout'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)


@app.route('/checkouts/<transaction_id>', methods=['GET'])
def show_checkout(transaction_id):
    transaction = find_transaction(transaction_id)
    result = {}
    if transaction.status in TRANSACTION_SUCCESS_STATUSES:
        result = {
            'header': 'Success!',
            'icon': 'success',
            'message': 'Your transaction has been successfully processed.'
        }
    else:
        result = {
            'header': 'Transaction Failed',
            'icon': 'fail',
            'message': 'Your test transaction has a status of ' + transaction.status + '.'
        }

    return render_template('checkouts/show.html', transaction=transaction, result=result)
