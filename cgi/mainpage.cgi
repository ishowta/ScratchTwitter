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
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';

sub mainpage_operator {
	# Config
	my $MAIN_PAGE_TMPL_PATH = '../tmpl/mainpage.tmpl';
	my $LOGIN_PAGE_TMPL_PATH = '../tmpl/login.tmpl';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name =  HTML::Entities::encode_entities(decode_utf8($CGI->cookie('user_name')));
	my $user_password =  HTML::Entities::encode_entities(decode_utf8($CGI->cookie('user_password')));

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->cookie('user_name')) || !(defined $CGI->cookie('user_password'))){
		$status_code = '200';
		$mode = 'jumpLoginPage';
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
		}else{
			# メインページを表示
			# Load tmpl
			my $main_page_tmpl = HTML::Template->new(
				filename => $MAIN_PAGE_TMPL_PATH,
				utf8 => 1
			);
			# Get tweet
			$sth = $dbh->prepare('SELECT * FROM tweet LEFT JOIN user ON tweet.user_id = user.id ORDER BY time DESC LIMIT 10');
			$sth->execute();
			$result = $sth->fetchall_arrayref(+{});
			# Put Tweet
			my @tweets = ();
			foreach my $raw_tweet (@$result){
				my %tweet = (	'USER_NAME' => $raw_tweet->{'mail'},
								'TEXT'      => $raw_tweet->{'text'},
								'TIME'      => $raw_tweet->{'time'}
							);
				if($raw_tweet->{'mail'} eq $user_name){
					$tweet{'ERASE_TWEET_ZONE'} = '<a href="#" class="close"><span class="glyphicon glyphicon-remove text-danger"></span></a>';
				}
				push @tweets, \%tweet;
			}
			$main_page_tmpl->param('TIMELINE_LOOP' => \@tweets);
			# Set Header
			print $CGI->header(@HEADER), $main_page_tmpl->output;
			return;
		}
	}elsif($mode eq 'jumpLoginPage'){
		# Add location
		push @HEADER , ('-location',"login.cgi");
		print $CGI->header(@HEADER);
	}

}

mainpage_operator();
