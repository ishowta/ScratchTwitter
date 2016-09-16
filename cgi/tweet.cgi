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
	$referer =~ s/\?(&|)tweet_empty_error=1//g;
	$referer =~ s/\?(&|)page=[0-9]*//g;

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->cookie('user_name')) || !(defined $CGI->cookie('user_password')) || !(defined $CGI->param('plain_tweet'))){
		$status_code = '302';
		$mode = 'jumpMainPage';
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

		# ツイートが不正だったらエラーを表示
		if(!Utils::isValidTweetText($plain_tweet)){
			push @HEADER , ('-location',$referer.'?&tweet_error=1');

			# Add cookie
			my $cookie_just_before_text = new CGI::Cookie(-name=>'just_before_tweet',-value=>$plain_tweet);
			push @HEADER , ('-cookie',[$cookie_just_before_text]);

			print $CGI->header(@HEADER);
			return;
		# 空でもエラー
		}elsif($plain_tweet =~ /^\s*$/){
			push @HEADER , ('-location',$referer.'?&tweet_empty_error=1');

			print $CGI->header(@HEADER);
			return;
		}

		# ID取得
		my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',{mysql_enable_utf8 => 1});
		my $sth = $dbh->prepare('SELECT id FROM user WHERE mail = ? AND password = ?');
		$sth->execute($user_name, $user_password);
		my $result = $sth->fetchall_arrayref(+{});
		my $user_id = $result->[0]->{'id'};

		# ツイート投稿
		my $encoded_tweet = Utils::encodeHTMLMulti($plain_tweet);
		my $dt = DateTime->now(time_zone => 'Asia/Tokyo');
		$sth = $dbh->prepare('INSERT INTO tweet VALUES (NULL, ?, ?, ?)');
		$sth->execute($user_id, $encoded_tweet, $dt);


		# Add location
		push @HEADER , ('-location',$referer);

		print $CGI->header(@HEADER);

	}elsif($mode eq 'jumpMainPage'){

		# Add location
		push @HEADER , ('-location',$MAIN_PAGE_CGI_PATH);

		# Set Header
		print $CGI->header(@HEADER);
	}

}

tweet_operator();
