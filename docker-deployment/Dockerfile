FROM public.ecr.aws/lambda/python@sha256:1f856e969af695d6524cbc2bed3691bd9834744b84f63da1b66218574946ce43 as build
RUN dnf install -y unzip && \
    curl -Lo "/tmp/chromedriver-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/121.0.6167.85/linux64/chromedriver-linux64.zip" && \
    curl -Lo "/tmp/chrome-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/121.0.6167.85/linux64/chrome-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
    unzip /tmp/chrome-linux64.zip -d /opt/

FROM public.ecr.aws/lambda/python@sha256:1f856e969af695d6524cbc2bed3691bd9834744b84f63da1b66218574946ce43 
RUN dnf install -y atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm
RUN pip install selenium==4.40.0
COPY --from=build /opt/chrome-linux64 /opt/chrome
COPY --from=build /opt/chromedriver-linux64 /opt/
COPY main.py ./
COPY requirements.txt ./
COPY __init__.py ./
COPY ./tabroom_summary ./tabroom_summary

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
# Make sure Python scripts in ./tabroom_summary are executable
# RUN chmod -R +x ./tabroom_summary

CMD [ "main.handler" ]


