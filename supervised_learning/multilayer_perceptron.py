from __future__ import print_function
from sklearn import datasets
import sys
import os
import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import helper functions
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path + "/../utils")
from data_manipulation import train_test_split, categorical_to_binary, normalize, binary_to_categorical
from data_operation import accuracy_score
sys.path.insert(0, dir_path + "/../unsupervised_learning/")
from principal_component_analysis import PCA


# Activation function
def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# Gradient of activation function
def sigmoid_gradient(x):
    return sigmoid(x) * (1 - sigmoid(x))


class MultilayerPerceptron():
    """Multilayer Perceptron classifier. A neural network with one hidden layer.
    Uses the sigmoid functions as the activation function of the hidden and output
    layer.

    Parameters:
    -----------
    n_hidden: int:
        The number of processing nodes (neurons) in the hidden layer. 
    n_iterations: float
        The number of training iterations the algorithm will tune the weights for.
    learning_rate: float
        The step length that will be used when updating the weights.
    early_stopping: boolean
        Whether to stop the training when the validation error has increased for a
        certain amounts of training iterations. Combats overfitting.
    plot_errors: boolean
        True or false depending if we wish to plot the training errors after training.
    """
    def __init__(self, n_hidden, n_iterations=3000, learning_rate=0.01, early_stopping=False, plot_errors=False):
        self.n_hidden = n_hidden    # Number of hidden neurons
        self.W = None               # Hidden layer weights
        self.V = None               # Output layer weights
        self.biasW = None           # Hidden layer bias
        self.biasV = None           # Output layer bias
        self.n_iterations = n_iterations
        self.learning_rate = learning_rate
        self.plot_errors = plot_errors
        self.early_stopping = early_stopping

    def fit(self, X, y):
        X_train = X
        y_train = y

        if self.early_stopping:
            # Split the data into training and validation sets
            X_train, X_validate, y_train, y_validate = train_test_split(X, y, test_size=0.1)
            y_validate = categorical_to_binary(y_validate)

        # Convert the nominal y values to binary
        y_train = categorical_to_binary(y_train)

        n_samples, n_features = np.shape(X_train)
        n_outputs = np.shape(y_train)[1]

        # Initial weights between [-1/sqrt(N), 1/sqrt(N)]
        a = -1 / math.sqrt(n_features)
        b = -a
        self.W = (b - a) * np.random.random((n_features, self.n_hidden)) + a
        self.biasW = (b - a) * np.random.random((1, self.n_hidden)) + a
        self.V = (b - a) * np.random.random((self.n_hidden, n_outputs)) + a
        self.biasV = (b - a) * np.random.random((1, n_outputs)) + a

        training_errors = []
        validation_errors = []
        iter_with_rising_val_error = 0
        for i in range(self.n_iterations):

            # Calculate hidden layer
            hidden_input = X_train.dot(self.W) + self.biasW
            hidden_output = sigmoid(hidden_input)
            # Calculate output layer
            output_layer_input = hidden_output.dot(self.V) + self.biasV
            output = sigmoid(output_layer_input)

            # Calculate the error
            error = y_train - output
            mse = np.mean(np.power(error, 2))
            training_errors.append(mse)

            # Calculate loss gradients:
            # Gradient of squared loss w.r.t each parameter
            v_gradient = -2 * (y_train - output) * \
                sigmoid_gradient(output_layer_input)
            biasV_gradient = v_gradient
            w_gradient = v_gradient.dot(
                self.V.T) * sigmoid_gradient(hidden_input)
            biasW_gradient = w_gradient

            # Update weights
            # Move against the gradient to minimize loss
            self.V -= self.learning_rate * hidden_output.T.dot(v_gradient)
            self.biasV -= self.learning_rate * np.ones((1, n_samples)).dot(biasV_gradient)
            self.W -= self.learning_rate * X_train.T.dot(w_gradient)
            self.biasW -= self.learning_rate * np.ones((1, n_samples)).dot(biasW_gradient)

            if self.early_stopping:
                # Calculate the validation error
                error = y_validate - self._calculate_output(X_validate)
                mse = np.mean(np.power(error, 2))
                validation_errors.append(mse)

                # If the validation error is larger than the previous iteration increase
                # the counter
                if len(validation_errors) > 1 and validation_errors[-1] > validation_errors[-2]:
                    iter_with_rising_val_error += 1
                    # If the validation error has been for more than 50 iterations
                    # stop training to avoid overfitting
                    if iter_with_rising_val_error > 50:
                        break
                else:
                    iter_with_rising_val_error = 0


        # Plot the training error
        if self.plot_errors:
            if self.early_stopping:
                # Training and validation error plot
                training, = plt.plot(range(i+1), training_errors, label="Training Error")
                validation, = plt.plot(range(i+1), validation_errors, label="Validation Error")
                plt.legend(handles=[training, validation])
            else:
                training, = plt.plot(range(i+1), training_errors, label="Training Error")
                plt.legend(handles=[training])
            plt.title("Error Plot")
            plt.ylabel('Error')
            plt.xlabel('Iterations')
            plt.show()

    def _calculate_output(self, X):
        # Calculate hidden layer
        hidden_input = X.dot(self.W) + self.biasW
        hidden_output = sigmoid(hidden_input)
        # Calculate output layer
        output_layer_input = hidden_output.dot(self.V) + self.biasV
        output = sigmoid(output_layer_input)

        return output

    # Use the trained model to predict labels of X
    def predict(self, X):
        output = self._calculate_output(X)
        # Predict as the indices of the highest valued outputs
        y_pred = np.argmax(output, axis=1)
        return y_pred


def main():
    data = datasets.load_digits()
    X = normalize(data.data)
    y = data.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, seed=1)

    # MLP
    clf = MultilayerPerceptron(n_hidden=10,
        n_iterations=5000,
        learning_rate=0.01, 
        early_stopping=True,
        plot_errors=True)

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)

    print ("Accuracy:", accuracy)

    # Reduce dimension to two using PCA and plot the results
    pca = PCA()
    pca.plot_in_2d(X_test, y_pred, title="Multilayer Perceptron", accuracy=accuracy, legend_labels=np.unique(y))

if __name__ == "__main__":
    main()
