# Automation

## Set-up
*The following assumes linux and admin/sudo priveleges.*

To download firefox: `sudo apt install firefox`.

To setup geckodriver to use with firefox and selenium ([reference](https://askubuntu.com/questions/870530/how-to-install-geckodriver-in-ubuntu)), find the latest geckodriver link from [here](https://askubuntu.com/questions/870530/how-to-install-geckodriver-in-ubuntu) and then:
```
wget <<https://github.com/.../geckodriver-v???-linux64.tar.gz>>
tar -xvzf geckdriver*
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
```
