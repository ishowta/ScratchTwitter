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
use POSIX 'ceil';
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';
require 'timeline.pl';

sub page_operator {
	# Config
	my $MAIN_PAGE_TMPL_PATH = '../tmpl/mainpage.tmpl';
	my $LOGIN_PAGE_TMPL_PATH = '../tmpl/login.tmpl';
	my $LOGIN_PAGE_CGI_PATH = 'login.cgi';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name =  decode_utf8($CGI->cookie('user_name'));
	my $user_password =  decode_utf8($CGI->cookie('user_password'));

	# Get param
	my $page = decode_utf8($CGI->param('page')) // 1;
	if($page !~ /^[1-9][0-9]*$/){
		$page = 1;
	}

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->cookie('user_name')) || !(defined $CGI->cookie('user_password'))){
		$status_code = '200';
		$mode = 'jumpLoginPage';
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
		# Connect DBI
		my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',
		{
			mysql_enable_utf8 => 1
		});
		my $sth;
		my $result;
		# Login Check
		$sth = $dbh->prepare('SELECT COUNT(*), id FROM user WHERE mail = ? AND password = ?');
		$sth->execute($user_name, $user_password);
		$result = $sth->fetchall_arrayref(+{});
		my $isPasswordDuplicate = $result->[0]->{'COUNT(*)'};
		# パスワードが間違っていたら400
		if($isPasswordDuplicate eq '0'){
			push @HEADER , ('-status', '400');
			print $CGI->header(@HEADER);
			return;
		}else{
			my $user_id = $result->[0]->{'id'};
			# メインページを表示
			# Load tmpl
			my $main_page_tmpl = HTML::Template->new(
				filename => $MAIN_PAGE_TMPL_PATH,
				utf8 => 1
			);

			# Get tweet
			$sth = $dbh->prepare('SELECT tweet.id as id, tweet.user_id as user_id, tweet.text as text, tweet.time as time, user.mail as mail FROM tweet LEFT JOIN user ON tweet.user_id = user.id ORDER BY time DESC LIMIT ?, 15');
			$sth->execute(($page-1) * 15);
			$result = $sth->fetchall_arrayref(+{});


			# Count tweet
			$sth = $dbh->prepare('SELECT COUNT(*) FROM tweet');
			$sth->execute();
			my $raw_count_data = $sth->fetchall_arrayref(+{});
			my $tweet_count = $raw_count_data->[0]->{'COUNT(*)'};

			# Make TimeLine
			my $timeline_tmpl = makeTimeLine($result, $user_id, $page, ceil($tweet_count/15));
			$main_page_tmpl->param('TIMELINE_TMPL' => $timeline_tmpl->output);

			# Set Header
			print $CGI->header(@HEADER), $main_page_tmpl->output;
			return;
		}
	}elsif($mode eq 'jumpLoginPage'){
		# Add location
		push @HEADER , ('-location',$LOGIN_PAGE_CGI_PATH);
		print $CGI->header(@HEADER);
	}

}

page_operator();
