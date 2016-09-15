#!/usr/bin/perl

use strict;
use utf8;
use CGI;
use CGI::Cookie;
use DBI;
use lib ('/home/takahashi/perl/local/lib/perl5');
use HTML::Template;
use HTML::Entities;
use Encode;
use Data::Dumper;
use DateTime;
use File::Copy;
use File::Basename;
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';

sub tweet_operator {
	# Config
	my $MAIN_PAGE_TMPL_PATH = '../tmpl/mainpage.tmpl';
	my $MAIN_PAGE_CGI_PATH = 'mainpage.cgi';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name = decode_utf8($CGI->cookie('user_name'));
	my $user_password = decode_utf8($CGI->cookie('user_password'));

	# Get param
	my $plain_tweet = ($CGI->param('plain_tweet'));

	# Get referer
	my $referer = decode_utf8($CGI->referer());
	$referer =~ s/\?(&|)tweet_error=1//g;
	$referer =~ s/\?(&|)tweet_pic_error=1//g;
	$referer =~ s/\?(&|)page=[0-9]*//g;

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->cookie('user_name')) || !(defined $CGI->cookie('user_password')) || !(defined $CGI->param('plain_tweet'))){
		$status_code = '400';
		$mode = 'fail';
	}else{
		$status_code = '200';
		$mode = 'showPage';
	}
	my @HEADER = (
			-type => 'text/html',
			-charset => "utf-8",
			-status => $status_code
		);

	# Body
	if($mode eq 'showPage'){

		# ログインチェック
		my $user_id;
		if(($user_id = Utils::checkAccount($user_name, $user_password)) == -1){
			# パスワードが間違っていたので400
			push @HEADER , ('-status', '400');
			print $CGI->header(@HEADER);
			return;
		}

		# 「set icon」ならアイコンを追加
		if($plain_tweet eq 'set icon'){

			# ...の前に画像が存在するかチェック
			if(defined($CGI->upload('pic'))){
				my $image_file_path = $CGI->param('pic');
				my $image_extension = $1 if $image_file_path =~ /\.(.{3,4})$/;
				if($image_extension =~ /^(gif|png|jpg|jpeg|bmp)$/i){

					### あった

					my $image_file_handler = $CGI->upload('pic');
					my $file_path = '../icon/'.$user_id.'.'.$image_extension;

					# userテーブルにurlを追加
					my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',{mysql_enable_utf8 => 1});
					my $sth = $dbh->prepare('UPDATE user SET icon = ? WHERE id = ?');
					$sth->execute($file_path, $user_id);
					$dbh->disconnect;

					# iconに保存
					my $fn = $file_path;
					my $fh = $image_file_handler;
					copy ($fh, $fn);
				}else{
					push @HEADER , ('-location',$referer.'?&tweet_pic_error=1');

					# Add cookie
					my $cookie_just_before_text = new CGI::Cookie(-name=>'just_before_tweet',-value=>$plain_tweet);
					push @HEADER , ('-cookie',[$cookie_just_before_text]);

					print $CGI->header(@HEADER);
					return;
				}
			}
		}else{
			# ツイートが不正だったらエラーを表示
			if(!Utils::isValidTweetText($plain_tweet)){
				push @HEADER , ('-location',$referer.'?&tweet_error=1');

				# Add cookie
				my $cookie_just_before_text = new CGI::Cookie(-name=>'just_before_tweet',-value=>$plain_tweet);
				push @HEADER , ('-cookie',[$cookie_just_before_text]);

				print $CGI->header(@HEADER);
				return;
			}

			# 画像
			my $has_pic = 0;
			my $file_path = '';
			if(defined($CGI->upload('pic'))){
				my $image_file_path = $CGI->param('pic');
				my $image_extension = $1 if $image_file_path =~ /\.(.{3,4})$/;
				if($image_extension =~ /^(gif|png|jpg|jpeg|bmp)$/i){
					$has_pic = 1;
					my $image_file_handler = $CGI->upload('pic');
					my $file_id = int(rand(10000000000000000000));
					$file_path = '../pic/'.$user_id.'_'.$file_id.'.'.$image_extension;
					# picに保存
					my $fn = $file_path;
					my $fh = $image_file_handler;
					copy ($fh, $fn);
				}else{
					push @HEADER , ('-location',$referer.'?&tweet_pic_error=1');

					# Add cookie
					my $cookie_just_before_text = new CGI::Cookie(-name=>'just_before_tweet',-value=>$plain_tweet);
					push @HEADER , ('-cookie',[$cookie_just_before_text]);

					print $CGI->header(@HEADER);
					return;
				}
			}

			# ツイート投稿
			my $encoded_tweet = Utils::encodeHTMLMulti($plain_tweet);
			warn $encoded_tweet;
			my $dt = DateTime->now(time_zone => 'Asia/Tokyo');
			my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',{mysql_enable_utf8 => 1});
			if($has_pic == 1){
				my $sth = $dbh->prepare('INSERT INTO tweet VALUES (NULL, ?, ?, ?, ?)');
				$sth->execute($user_id, $encoded_tweet, $dt, $file_path);
			}else{
				my $sth = $dbh->prepare('INSERT INTO tweet VALUES (NULL, ?, ?, ?, NULL)');
				$sth->execute($user_id, $encoded_tweet, $dt);
			}
		}

		# Add location
		push @HEADER , ('-location',$referer);

		print $CGI->header(@HEADER);

	}elsif($mode eq 'fail'){

		print $CGI->header(@HEADER);
	}

}

tweet_operator();
