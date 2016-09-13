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

sub mainpage_operator {
	# Config
	my $USER_PAGE_TMPL_PATH = '../tmpl/searchpage.tmpl';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name =  HTML::Entities::encode_entities(decode_utf8($CGI->cookie('user_name')));
	my $user_password =  HTML::Entities::encode_entities(decode_utf8($CGI->cookie('user_password')));

	# Get param
	my $search_text =  HTML::Entities::encode_entities(decode_utf8($CGI->param('text')));

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->param('text'))){
		$status_code = '403';
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
		# Connect DBI
		my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',
		{
			mysql_enable_utf8 => 1
		});
		my $sth;
		my $result;

		if(defined $CGI->cookie('user_name') && defined $CGI->cookie('user_password')){
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
			}
		}
		# メインページを表示
		# Load tmpl
		my $user_page_tmpl = HTML::Template->new(
			filename => $USER_PAGE_TMPL_PATH,
			utf8 => 1
		);
		# Get tweet
		$sth = $dbh->prepare('SELECT tweet.id as id, tweet.text as text, tweet.time as time, user.mail as mail FROM tweet LEFT JOIN user ON tweet.user_id = user.id WHERE tweet.text LIKE ? ORDER BY time DESC LIMIT 10');
		$sth->execute('%'.$search_text.'%');
		$result = $sth->fetchall_arrayref(+{});
		# Put Tweet
		my @tweets = ();
		foreach my $raw_tweet (@$result){
			my %tweet = (	'USER_URL' => '<a href="userpage.cgi?user='.$raw_tweet->{'user_id'}.'">'.$raw_tweet->{'mail'}.'</a>',
							'TEXT'      => $raw_tweet->{'text'},
							'TIME'      => $raw_tweet->{'time'}
						);
			if(defined $CGI->cookie('user_name') && $raw_tweet->{'mail'} eq $user_name){
				$tweet{'ERASE_TWEET_ZONE'} = '<a href="delete.cgi?id='.$raw_tweet->{'id'}.'" class="close"><span class="glyphicon glyphicon-remove text-danger"></span></a>';
			}
			push @tweets, \%tweet;
		}
		$user_page_tmpl->param('TIMELINE_LOOP' => \@tweets);
		# Set Header
		print $CGI->header(@HEADER), $user_page_tmpl->output;
	}elsif($mode eq 'fail'){
		print $CGI->header(@HEADER);
	}

}

mainpage_operator();
