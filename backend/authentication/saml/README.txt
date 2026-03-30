Place your SAML SP private key here as sp-private-key.pem
This file is excluded from version control via .gitignore
Generate a self-signed key pair with:
  openssl req -x509 -newkey rsa:2048 -keyout sp-private-key.pem -out sp-certificate.crt -days 365 -nodes
