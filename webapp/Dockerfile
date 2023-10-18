FROM nikolaik/python-nodejs@sha256:08ff9735ee59d1ec5652aa53bc9101566f02af3d54442da35ebc4447cdc8f8f6 as base
USER pn
WORKDIR /home/pn/app
COPY --chown=1000:1000 . .
RUN npm ci

# App Development
FROM base as app-dev
USER pn
ENV NODE_ENV=development
CMD npm run dev

# App Production
FROM base as app-prod
USER pn
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build
CMD npm run start
