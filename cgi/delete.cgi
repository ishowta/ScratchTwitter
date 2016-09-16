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

sub delete_operator {
	# Config
	my $MAIN_PAGE_TMPL_PATH = '../tmpl/mainpage.tmpl';
	my $MAIN_PAGE_CGI_PATH = 'mainpage.cgi';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name = decode_utf8($CGI->cookie('user_name'));
	my $user_password = decode_utf8($CGI->cookie('user_password'));

	# Get param
	my $tweet_id = decode_utf8($CGI->param('id'));

	# Get referer
	my $referer = decode_utf8($CGI->referer());
	$referer =~ s/\?(&|)tweet_error=1//g;
	$referer =~ s/\?(&|)tweet_empty_error=1//g;
	$referer =~ s/\?(&|)page=[0-9]*//g;

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->cookie('user_name')) || !(defined $CGI->cookie('user_password')) || !(defined $CGI->param('id'))){
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

		# ツイートが存在するかチェック(存在しなければ消したことにする)
		my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',{mysql_enable_utf8 => 1});
		my $sth = $dbh->prepare('SELECT COUNT(*) FROM tweet WHERE id = ?');
		$sth->execute($tweet_id);
		my $result = $sth->fetchall_arrayref(+{});
		if($result->[0]->{'COUNT(*)'} == 1){
			# ツイートが本当にユーザーのものなのかチェック
			my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',{mysql_enable_utf8 => 1});
			my $sth = $dbh->prepare('SELECT user_id FROM tweet WHERE id = ?');
			$sth->execute($tweet_id);
			my $result = $sth->fetchall_arrayref(+{});
			if(length(@$result) != 1 || $result->[0]->{'user_id'} != $user_id){
				push @HEADER , ('-status', '400');
				print $CGI->header(@HEADER);
				return;
			}

			# ツイート削除
			my $dt = DateTime->now(time_zone => 'Asia/Tokyo');
			$sth = $dbh->prepare('DELETE FROM tweet WHERE id = ?');
			$sth->execute($tweet_id);
		}

		# Add location
		push @HEADER , ('-location',$referer);

		print $CGI->header(@HEADER);

	}elsif($mode eq 'fail'){

		print $CGI->header(@HEADER);
	}

}

delete_operator();
