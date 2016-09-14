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
	my $plain_tweet = decode_utf8($CGI->param('plain_tweet'));

	# Get referer
	my $referer = decode_utf8($CGI->referer());
	$referer =~ s/\?tweet_error=1//g;

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->cookie('user_name')) || !(defined $CGI->cookie('user_password')) || !(defined $CGI->param('plain_tweet'))){
		$status_code = '400';
		$mode = 'fail';
	}else{
		$status_code = '200';
		$mode = 'showMainPage';
	}
	my @HEADER = (
			-type => 'text/html',
			-charset => "utf-8",
			-status => $status_code
		);

	# Body
	if($mode eq 'showMainPage'){
		# Connect DBI
		my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',
		{
			mysql_enable_utf8 => 1
		});
		my $sth;
		my $result;
		# Login Check
		$sth = $dbh->prepare('SELECT COUNT(*) FROM user WHERE mail = ? AND password = ?');
		$sth->execute($user_name, $user_password);
		$result = $sth->fetchall_arrayref(+{});
		my $isPasswordDuplicate = $result->[0]->{'COUNT(*)'};
		# パスワードが間違っていたら400
		if($isPasswordDuplicate eq '0'){
			push @HEADER , ('-status', '400');
			print $CGI->header(@HEADER);
			return;
		}

		# ツイートが不正だったらエラーを表示
		if(!Utils::isValidTweetText($plain_tweet)){
			push @HEADER , ('-location',$referer.'?tweet_error=1');
			print $CGI->header(@HEADER);
			return;
		}

		# ID取得
		$sth = $dbh->prepare('SELECT id FROM user WHERE mail = ? AND password = ?');
		$sth->execute($user_name, $user_password);
		$result = $sth->fetchall_arrayref(+{});
		my $user_id = $result->[0]->{'id'};
		# ツイート投稿
		my $dt = DateTime->now(time_zone => 'Asia/Tokyo');
		$sth = $dbh->prepare('INSERT INTO tweet VALUES (NULL, ?, ?, ?)');
		$sth->execute($user_id, $plain_tweet, $dt);
		# Add location
		push @HEADER , ('-location',$referer);
		print $CGI->header(@HEADER);

	}elsif($mode eq 'fail'){
		print $CGI->header(@HEADER);
	}

}

tweet_operator();
