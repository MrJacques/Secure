## Introduction

I set a goal to create a secure and simple backup using a spare raspberry pi and external hard drive.  It didn’t need to be fast or encrypt the backup. I did want something secure, so no software on the clients (machines being backed up.)  To begin with, I would be backing up linux machines over a LAN so using rsync seems to be a natural choice.

Security was a very important consideration.  The goal was to have a raspberry pi running with the absolute minimum number of open ports.  The pi should be able to reach out but nothing could connect to the pi.  Since the pi would be running headless, there would be an SSH server running and exposed but nothing else.  

Here are main requirements:

-   Use a raspberry pi (although any dedicated linux machine would work)
-   Use a spare external hard drive (again, speed is not an issue.)
-   Back up important files.  No requirement to make a backup that could be used to restore the backed up machines, just important files.  No need to backup links, file attributes or anything but the files and directories. (This is why the external hard drive file system does not matter and is not changed.)
-   Secure (block all incoming network request except a single secured SSH port)
-   No software or configuration changes on the machines being backed up
-   Keep old copies of files, kinda like the time machine.   This is also a very important security configuration.  The backup should not be broken by ransomware on the client overwriting the files to be backed up a few millions times.  It should always be possible to go back to the old backup files and recover a version of the lost or encrypted file.
-   Smart duplicate file detection with the daily backups to preserve hard drive space.  Moving or renaming files should not result in multiple copies of files being backed up and kept.
-   Robust error checking
-   Send a text if there is an error
-   Have a canary in the coal mine to alert me if some test files that I don’t expect to  change are changed. 

## Standard raspberry pi setup

Start with a standard raspberry pi install and setup.

-   **Set hostname**: the name of your Pi. I
-   **Set username and password**: Pick the username and password you'll use for the Pi
-   **Enable SSH: This will be used to run the backup without a dedicated monitor**
-   **Use password authentication / public key**: Pick password authentication, it will be changed to use keys in a later step.
-   **Configure a network**: We will need a network (obviously.)
-   **Set locale settings**: Configure keyboard layout and timezone (probably chosen correctly by default)

## Change raspberry pi username from pi to something else

This is included if your pi is using pi as the username.  

We want to change the default username pi to something else to increase security.  I like to keep my preferred user id at the default uid of 1000, so I jump through a few extra steps to rename the pi username, not just create a new account.  

Since the pi is going to be running headless in my physical control I prefer to leave the auto-login turned on.

```bash
sudo adduser temp
sudo usermod temp -a -G sudo
su temp
exit

sudo reboot
```

login as temp

```bash
sudo usermod -l jp pi
sudo groupmod --new-name jp pi
sudo usermod -m -d /home/jp jp
reboot
```

login with new username

turn back on auto login

```bash
sudo userdel temp
rm -rf /home/temp
```

## Change External Hard Drive Name

I prefer to set a reasonable name for the external hard drive and not use the default manufacturer name.  It can make things easier to use a name without spaces or special characters.

I do not format the disk, only edit the file system name.

```bash
sudo apt-get install gnome-disk-utility
gnome-disks
```

Click on the partition to rename, then click on settings and select edit file system.  Rename the partition to Backup (uppercase B).

Unmount or unplug and the remount to check that the change was successful.

## Install sshfs and grsync

[_sshfs_](https://help.ubuntu.com/community/SSHFS) is used to mount remote file systems over ssh.  [_Grsync_](https://www.thegeekdiary.com/grsync-graphical-rsync-backup-tool-in-ubuntu-linux/) is a graphical wrapper on [_rsync_](https://help.ubuntu.com/community/rsync) (with a dependency on rsync)

After installing sshfs we will also generate the ssh keys that will be used to perform password less ssh logins on other machines.

```bash
sudo apt-get install sshfs grsync
ssh-keygen -t ecdsa -b 521
```

After generating the ssh keys, it is important to connect to all the machines you plan on backing up at least once as the user you will be connecting with.  This is shown in the next section.

>ECDSA is a type of public-key cryptography that uses elliptic curves to create and verify digital signatures. It's commonly used for secure communication over the internet, such as in SSH connections. The key length specifies the strength of the key, with longer keys generally being more secure but also taking longer to generate and use. A key length of 521 bits is considered very strong and is recommended for high-security applications.
{.is-info}


## Get fstab working

> An SSHFS mount is used with rsync rather than using ssh directly in rsync for enhanced security.  By using a read-only mount I reduce the chance of a misconfigured rsync deleting files on the machines to be backed up.
{.is-info}

In this step, get the remote drives mounted using fstab so they will always remount on boot.

First check uid and gid for the user account you will be using, both should be 1000 .

```bash
grep jp /etc/passwd /etc/group
```
Or
```bash
grep 1000 /etc/passwd /etc/group
```

Edit fstab as root.

```bash
sudo nano /etc/fstab
```

Add a line like the following to bottom (one long line)

```
RemoteUserID@RemoteHostname:/RemotePathToBackup/ /mnt/SimpleRemoteHostName/Data fuse.sshfs ro,delay_connect,_netdev,user,idmap=user,identityfile=/home/jp/.ssh/id_ecdsa,allow_other,default_permissions,uid=1000,gid=1000 0 0
```

The **RemoteUserID**, **RemoteHostnameand**, **RemotePathToBackup** and **SimpleRemoteHostName** all refer to the machine that is being backed up.  The remote hostname must be a valid network name, while the simple remote hostname can be a simplified name or nickname.  The final part of the mnt path **Data** should be replaced with something relevant for your setup.  The ```/home/**jp**``` is the home directory on the pi.

uid and gid should match your local (the pi) uid and gid.

>**This will create a read only mount**.  There should never be a reason for this machine to modify files on the remote machine.
{.is-warning}

For example, I used the following to connect to a local machine:

```
jp@baobob:/media/jp/Data/ /mnt/baobob/Data fuse.sshfs ro,delay_connect,_netdev,user,idmap=user,identityfile=/home/jp/.ssh/id_ecdsa,allow_other,default_permissions,uid=1000,gid=1000 0 0
```

Save the changes to fstab.

Use the following to create the local mount point directory

```bash
sudo mkdir -p /mnt/SimpleRemoteHostName/Data
```

At this point, the ssh keys need to be copied to the remote machine before mounting.

```bash
# Setup keys
ssh-copy-id RemoteUserID@RemoteHostname

# test the connection and exit
ssh RemoteUserID@RemoteHostname
exit 
```

Make sure that remote host ends up in the known host list for root.  i.e. We want the root account on the raspberry pi to recognize the remote host and have an entry for the remote host in the raspberry pi’s root account known host file.

You don't need to actually log on below, just confirm the remote host identity

```bash
sudo ssh RemoteUserID@RemoteHostname
```

Test the changes to fstab and that it is possible to mount the remote host.

```bash
sudo mount -a
ls /mnt/SimpleRemoteHostName/Data

# Confirm read only by trying to create a file
touch /mnt/SimpleRemoteHostName/Data/DeleteMe

# Unmount
sudo umount /mnt/SimpleRemoteHostName/Data
```

Repeat this process for each mount point needed on each remote machine.

## Turn off password prompt for sudo mount -a

Turn off the password prompt when using the sudo mount -a command.  This will allow the actual backup script to run mount -a without the entire script needing to be run with elevated privileges.

To configure the system to not prompt for a password when running the a command, you can modify the [_sudoers_](https://help.ubuntu.com/community/Sudoers) file using the "visudo" command.

```bash
sudo visudo
```

This will open the "```sudoers```" file in the system's default text editor. Next, add the following line to the end of the file:

```bash
yourusername ALL=(ALL) NOPASSWD: /bin/mount -a
```

Make sure to replace **yourusername** with actual username  on the pi.

## Install Python 3.9 (or better)

At the time this document was created, python 3.9 was not installed by default on the raspberry pi and could not be installed with apt-get.  The scripts use typing that is only available in python  3.9 or later.

You can test the python version installed (or if it is installed) by using the following:

python --version

I used the following guide to compile and install python 3.9 on the raspberry pi:

[_https://community.home-assistant.io/t/python-3-9-install-on-raspberry-pi-os/241558_](https://community.home-assistant.io/t/python-3-9-install-on-raspberry-pi-os/241558)

[_python3 -m pip install typing_](https://community.home-assistant.io/t/python-3-9-install-on-raspberry-pi-os/241558)

## Install python requirements

I didn’t bother with a virtual environment on the raspberry pi.  All packages were installed for all users.

```bash
sudo python3.9 -m pip install --upgrade pip

sudo python3.9 -m pip install -r requirements.txt
# or
sudo python3.9 -m pip install twilio
```

## Configure texting

The scripts are set up to text if there is an error.  The Twilio API is used to implement the texting.

You can get a free trial account at [_www.twilio.com/referral/ft9Jn1_](http://www.twilio.com/referral/ft9Jn1)

That includes my referral code with Twilio which will earn me some free text if you end up paying for an account.

Once you sign up, rename the ```twilio-sample.json``` to ```twilio.json``` and then edit with your information. The phones you want to send to will need to be authorized on Twilio.

```json
{
   "twilio": {
       "notes": "to get free account - www.twilio.com/referral/ft9Jn1",
       "account_sid": "Put twilio account sid here",
       "auth_token": "Put authentication token here",
       "from_phone": "+15552134567",
       "to_phones": [
           "+15552134568",
           "+15552134569"
       ],
       "test": {
           "account_sid": "Put test twilio account sid here",
           "auth_token": "Put test authentication token here",
           "test_from": "+15552134560"
       }
   }
}
```

Test the configuration by running ```TestOnError.py```

```bash
cd sbackup
python3.9 python/TestOnError.py --help

# this should pass
python3.9 python/TestOnError.py ping -n localhost 

# this should fail and send a text message
python3.9 python/TestOnError.py ping -n this.will.fail
```

## Canary

The idea behind the canary is to find unexpected changes to files to detect ransomware or other problems.  

Nothing complicated here, pick as many random files as needed to have confidence that problems will be found quickly.  I started with the RandimFilePicker.py to pick a bunch of files for each extension then trimmed the list to something manageable.  The idea was to pick files that I would not expect to change but I would expect a ransomware script to modify.  So things like doc files, pictures, media, etc. 

Once there is a list of files, create the md5 file.  I suggest using the full absolute path (on the backup hard drive on the pi) in the list of files.  Given a files.txt file with a filename on each line, use the following to create a canary.md5 file:

```bash
xargs -a files.txt -L1 -d '\n' md5sum > canary.md5

# test the md5 file
md5sum -c canary.md5
# or
python3.9 python/TestOnError.py md5sum --quiet -c canary.md5
```

This will be used to send a text if any of the files in canary.md5 are modified.

The md5 file is checked with the following command:

```bash
ONERR="python3.9 python/TextOnError.py"
${ONERR} md5sum --quiet -c canary.md5 
```

## rsync-backup Script 

The rsync-backup.csh script accepts a directory to backup, a destination to backup to and, optionally, a list of files and directories to exclude.  The script then does some error checking before calling rsync.

The following options are used when calling rsync.  

```bash
rsync -r -t --no-compress -delete -s --itemize-changes --backup  --backup-dir=${BACKUP_DIR} --exclude-from ${EXCLUDE_FILE} ${SOURCE} ${DESTINATION}
```

The ```--backup``` and ```--backup-dir``` will move deleted or changed files from the backup destination into the ```BACKUP_DIR```.  This is used to keep track of changes to files.  The backup directory will look like this:

```bash
DAY=$(date +"%Y-%m-%d")
BACKUP_DIR="$DESTINATION/old/${DAY}"
```

If, for example, there is a file that changes daily and the backup script is run daily, then the backup directory will contain a copy of the file as it existed on the day of the backup.

The ```--itemize-changes``` option will print out a log of all the files created, changed or deleted.  

The ```--no-compress``` option is used because rsyncing over a local network is fast compared to the Raspberry Pi zero CPU.  Compression when moving data over a LAN and WiFi using a Raspberry Pi would just slow things down.

The ```-t``` option preserves the modification time on files being backed up.

## Collapse Script

The rsync-backup script uses the backup option to keep daily versions of files changed or deleted.  The collapse script “collapses” the daily changes into daily, weekly, monthly and yearly folders.

The basic philosophy behind collapse is to keep at least X daily backups, then continue keeping daily backups till a Saturday is reached (starting at today and moving backwards in time.)  Then keep weekly backups for a defined number of weeks, then move to monthly backups once the end of the month is reached.  Same thing for monthly backups.  Finally yearly backups are kept forever.

The default is a minimum of 7 daily backups, a minimum of 4 weekly backups, and a minimum 12 monthly backups.  These values can be customized.

When collapsing directories the contents of the oldest directories will be kept.  It assumes that backup directories have the date in the name, and that older directories are not being added/created out of order.  

## DeleteDuplicates Script

I know what people will say, why reinvent the wheel there are already ways to de-duplicate.  I want to look for duplicates in multiple directories but only delete in specific directories.  It would also be advantgous to implement a caching system.  Finally it needed to take care to be efficient and only calculate md5 hashes when actually needed.

The DeleteDuplicates program starts with a list of primary and secondary directories.The primary directories are the backup destinations and *never* (repeat never) have files deleted from them.  Secondary directories are the daily backups of changed files. A file in a secondary directory will be deleted if a duplicate is found in a primary directory or (a younger) duplicate is found in this or another secondary directory.  i.e No files in the secondary directories should have duplicates when finished.

Md5 hashes will only be calculated for groups of files having the same size (where at least one of the files is in a secondary directory.)

There is a pretend option ```--pretend``` that will show what would have been deleted without actually deleting.

## Backup Script

Here is the script that brings it all together and is run daily.  It should not be run past midnight as the daily backup dates will not work correctly.

```bash
#!/bin/bash

# Uncomment to stop script on error
#set -euo pipefail

cd /home/xx/sbackup

#ONERR="python3.9 python/TextOnError.py"
ONERR=""

# Use "sudo visudo" to tell sudo not to ask
# for a password for the mount -a command.
# and then add the below to the end of the file:
# username ALL=(root) NOPASSWD: /bin/mount -a
# Using the username that will run the backup
sudo mount -a

# Want to stop if these source directories are
# empty.
MOUNTS="/mnt/baobob-home
/mnt/bonsai-home"

for f in $MOUNTS
do
    ${ONERR} mountpoint "$f"
    if [ `ls -a1 "$f" | wc -l` -le 2 ] ; then
      echo "Directory is empty $f, check if mounted"
      ${ONERR} --always -m "Directory is empty $f, check if mounted"
      exit 10
    fi

    # $f has content
done

# Check that everything is mounted
${ONERR} mountpoint /media/xx/Backup/
${ONERR} mountpoint /mnt/baobob-home
${ONERR} mountpoint /mnt/bonsai-home

${ONERR} ./rsync-backup.csh /mnt/baobob-home /media/xx/Backup exclude-baobob.txt
${ONERR} ./rsync-backup.csh /mnt/bonsai-home /media/xx/Backup exclude-bonsai.txt

echo Collapse /media/xx/Backup/old/
${ONERR} python3.9 python/Collapse.py -v /media/xx/Backup/old/

echo Dup Check -p /media/xx/Backup/ -s /media/xx/Backup/old/
${ONERR} python3.9 python/DuplicateDelete.py -v -s /media/xx/Backup/old/ -p /media/xx/Backup/

echo Canary Check
${ONERR} md5sum --quiet -c canary.md5 
```

If you want to stop on errors, then you will probably want to check the mount points before calling ```rsync```.

```rsync-backup``` will check that the mount is not empty before trying to rsync with a backup directory.

The duplicate delete script will only delete duplicates in the daily backups.

## Set up crontab

[_Crontab_](https://help.ubuntu.com/community/CronHowto) is a utility program that enables users to schedule commands or scripts to run automatically at specific intervals or times. In this case, the line to be added will tell the system to run the full backup script at 1:00 AM every day (the 0 1 \* \* \* part specifies the time and frequency).  Replace the /home/**username** with the correct home directory and location on the pi.

Start with making the run-full-backup.vsh script executable:

```bash
chmod +x .home/username/sbackup/run-full-backup.csh
```

Then edit the crontab file:

1.  Open your crontab file by running the following command in your terminal:

```bash
crontab -e
```

2.  This will open your crontab file in a text editor. You can then add the following line at the end of the file:

```
0 1 * * * /home/username/sbackup/run-full-backup.csh
```

3.  Save the file and exit the text editor.

## Remove any authorized_keys

If you have authorized any machines to connect using a key instead of a password, now is the time to remove those authorizations.

If you want to revoke and remove all password-less ssh access to the pi, you can simply delete the ```~/.ssh/authorized_keys``` file on the pi.

```bash
rm ~/.ssh/authorized_keys
```

If you want to remove the key for a specific **machine** you can use the following command on the pi:  

```bash
sed -i '/machine/d' ~/.ssh/authorized_keys
```

Replace **machine** with the hostname that is having access revoked.

## Copy SSH key to USB

Our goal here is to create a new ssh key, authorize it to be used to log into the pi (remotely with ssh), and finally move the new ssh keys to a USB device for safe keeping. 

>if you lose the USB key, you can always use a monitor and keyboard to create a new key.
{.is-info}

These commands are run on the pi.

1.  Create a new private/public key pair.  You can use a pass-phrase if you would like.  I’ve used backup-pi as the base file, you can use anything you would like.

```bash
mkdir -p ~/key
chmod 700 ~/key
cd ~/key
ssh-keygen -t ecdsa -f backup-pi
```

2.  I like to give the private key an extension.  YMMV

```
mv backup-pi backup-pi.key
```

3.  Append the public key to the pi’s authorized keys file.

```
cat backup-pi.pub >> ~/.ssh/authorized_keys
```

3.  Move the private and public keys to a USB for safe keeping.  Delete (shred for the paranoid) the files on the pi.

5.  You can now use the following command to ssh into the pi from another machine:

```bash
ssh -i ~/path/to/usb/backup-pi.key piusername@pi-hostname
```

## Turn off SSH password login

Note: Before turning off password logins, make sure you have a working SSH key setup and have tested it from another machine. Otherwise, you may lose access to your server.  You can always use a keyboard and monitor, in case there is a problem.

1.  Edit the SSH daemon configuration file /etc/ssh/sshd_config.

```bash
sudo nano /etc/ssh/sshd_config
```

2.  Either find the ```#PasswordAuthentication yes``` and uncomment it (remove the #) and change it to ```PasswordAuthentication no``` or just create the line.

3.  Save and close the sshd_config file.

4.  Restart the SSH daemon to apply the changes:

```bash
sudo systemctl restart sshd
```

## Conclusion

At this point, your backup should be running daily on the pi with the crontab.

You have tested the text on error and are notified of any errors.

And finally, there is no way onto the pi except with the USB or a physical monitor.