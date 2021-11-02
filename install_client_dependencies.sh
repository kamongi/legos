# If python2.7 is not available and virtualenv
sudo apt install python-minimal virtualenv

# Then, create a virtualenv, in the project root directory. I.e., 
virtualenv local_dev --python=python2.7

# Activate it, I.e., 
source local_dev/bin/activate

# Install the pip packages from the requirements file
pip install -r requirements.txt

echo "USAGE: "
echo "$ source local_dev/bin/activate"
echo "python manager.py --AGUsername --AGPassword --AGHostIP --AGPort --repositoryName"