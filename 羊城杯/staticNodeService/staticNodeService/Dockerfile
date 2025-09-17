FROM node:latest

WORKDIR /App

COPY App/ .
COPY flag /flag
COPY readflag.c /readflag.c
COPY start.sh /start.sh

RUN npm install
RUN chown root:root /flag && chmod 400 /flag
RUN gcc -o /readflag /readflag.c
RUN chmod a+x /start.sh
RUN rm /readflag.c
RUN chmod u+s /readflag
RUN chown -R node:node /App

EXPOSE 3000

CMD [ "/bin/bash", "/start.sh" ]
