sudo apt update
sudo apt install -y python3 python3-venv python3-pip latexmk \
                    texlive-latex-base \
                    texlive-latex-extra \
                    texlive-pictures \
                    texlive-science


python3 -m venv venv
source venv/bin/activate
pip install jinja2 pydantic pyyaml