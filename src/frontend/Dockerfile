FROM node:21-bookworm AS build
WORKDIR /app
COPY . .
RUN cd /app \
    && npm install \
    && npm run build

FROM node:21-bookworm

# Create app directory
WORKDIR /usr/src/app

COPY --from=build /app/server/startup /opt/startup
COPY --from=build /app/server/startup/sshd_config /etc/ssh/
COPY --from=build /app/server /usr/src/app/server
COPY --from=build /app/dist /usr/src/app/server/public

# Install Tools - nscd is a DNS Cache
RUN apt-get update \
    && apt-get install -y net-tools nano openssh-server vim curl wget tcptraceroute nscd tcpdump dnsutils

RUN npm install -g pm2 \
    && echo "root:Docker!" | chpasswd \
    && echo "cd /usr/src/app" >> /etc/bash.bashrc \
    && cd /opt/startup \
    && chmod 755 /opt/startup/init_container.sh \
    && cd /usr/src/app/server \
    && npm install

EXPOSE 3000

ENV PM2HOME /pm2home

ENV PORT 3000
ENV WEBSITE_ROLE_INSTANCE_ID localRoleInstance
ENV WEBSITE_INSTANCE_ID localInstance
ENV PATH ${PATH}:/usr/src/app

ENV APP_HOME "/usr/src/app"

ENTRYPOINT ["/opt/startup/init_container.sh"]